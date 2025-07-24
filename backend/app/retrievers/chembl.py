import logging
from typing import Any

import requests
from chembl_webresource_client.new_client import new_client
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from more_itertools import unique

LOGGER = logging.getLogger(__name__)


class ChEMBLRetriever(BaseRetriever):
    """A retriever to fetch data from ChEMBL.

    Uses the chembl_webresource_client to fetch data from ChEMBL.
    See: https://github.com/chembl/chembl_webresource_client
    """

    max_count: int = 5

    def _retrieve_data(self, query: str) -> list[dict]:
        """Retrieve data from ChEMBL based on the given query, which could be either a ChEMBL ID or molecule name."""
        molecule = new_client.molecule
        results = []

        if query.upper().startswith("CHEMBL"):
            try:
                result = molecule.get(query)
                if result:
                    results = [result]
                else:
                    raise ValueError("ChEMBL ID not found")
            except ValueError:
                pass

        if not results:
            molecules = molecule.filter(pref_name__icontains=query).only(
                "molecule_chembl_id",
                "pref_name",
                "molecule_type",
                "molecule_properties",
            )[: self.max_count]
            results = list(molecules)

        return results

    def _retrieve_target_details(self, target_chembl_id: str) -> dict:
        """Fetch the target details using the target's ChEMBL ID."""
        target = new_client.target
        try:
            target_info = target.get(target_chembl_id)
            if target_info:
                return {
                    "target_name": target_info.get("pref_name", "Unknown"),
                    "target_type": target_info.get("target_type", "Unknown"),
                    "target_organism": target_info.get("organism", "Unknown"),
                }
        except Exception as e:
            LOGGER.error(
                f"Failed to fetch target details for {target_chembl_id}: {str(e)}"
            )
        return {
            "target_name": "Unknown",
            "target_type": "Unknown",
            "target_organism": "Unknown",
        }

    def _retrieve_mechanism_details(self, chembl_id: str) -> list[dict[str, Any]]:
        """Fetch the detailed drug mechanism information using the ChEMBL ID."""
        mechanism = new_client.mechanism
        mechanisms = mechanism.filter(molecule_chembl_id=chembl_id)

        mechanism_details = []

        for mech in mechanisms:
            target_chembl_id = mech.get("target_chembl_id", "Unknown")

            if target_chembl_id != "Unknown":
                target_details = self._retrieve_target_details(target_chembl_id)
            else:
                target_details = {
                    "target_name": "Unknown",
                    "target_type": "Unknown",
                    "target_organism": "Unknown",
                }

            details = {
                "mechanism_of_action": mech.get("mechanism_of_action", "Unknown"),
                "action_type": mech.get("action_type", "Unknown"),
                "target_chembl_id": target_chembl_id,
                **target_details,
            }
            mechanism_details.append(details)

        return mechanism_details

    def _retrieve_description(self, chembl_id: str) -> str:
        """Retrieve the description of the compound using the ChEMBL ID."""
        url = f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/"
        try:
            response = requests.get(url)
            if response.status_code == 200:

                return f"Description available at {url}"
            else:
                return "Description not found."

        except requests.RequestException as e:
            LOGGER.error(f"Failed to retrieve description for {chembl_id}: {str(e)}")
            return "Error retrieving description."

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any,
    ) -> list[Document]:
        LOGGER.debug(f"Querying ChEMBL for {query}")

        results = self._retrieve_data(query)
        results = list(unique(results, key=lambda r: r.get("molecule_chembl_id", r)))

        documents = []
        for data in results:
            chembl_id = data.get("molecule_chembl_id", data)
            if not chembl_id or not isinstance(chembl_id, str):
                LOGGER.warning("No ChEMBL ID found in the data")
                continue

            description = self._retrieve_description(chembl_id)

            mechanisms = self._retrieve_mechanism_details(chembl_id)

            doc = Document(
                id=chembl_id,
                metadata={
                    "chembl_id": chembl_id,
                    "name": data.get("pref_name", "Unknown"),
                    "molecule_properties": data.get("molecule_properties", {}),
                    "molecule_type": data.get("molecule_type", "Unknown"),
                    "mechanisms": mechanisms,
                },
                page_content=(
                    description
                    if len(description) > 20
                    else "No sufficient description found"
                ),
            )
            documents.append(doc)

        return documents


def get_chembl_retriever(max_count: int = 5) -> BaseRetriever:
    return ChEMBLRetriever(max_count=max_count)
