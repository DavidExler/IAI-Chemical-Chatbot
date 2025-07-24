import logging
from collections.abc import Iterable
from typing import Any

import pubchempy as pcp
import requests
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from more_itertools import unique

LOGGER = logging.getLogger(__name__)


class PubChemRetriever(BaseRetriever):
    domain: str = "compound"
    max_count: int = 5

    def _retrieve_data(self, query: str) -> list[pcp.Compound | pcp.Substance]:
        if self.domain == "compound":
            try:
                return [pcp.Compound.from_cid(int(query))]
            except ValueError:
                cids: list[int] = pcp.get_cids(
                    query, "name", self.domain, list_return="flat"
                )
                return [pcp.Compound.from_cid(cid) for cid in cids[: self.max_count]]
        elif self.domain == "substance":
            try:
                return [pcp.Substance.from_sid(int(query))]
            except ValueError:
                sids: list[int] = pcp.get_sids(
                    query, "name", self.domain, list_return="flat"
                )
                return [pcp.Substance.from_sid(sid) for sid in sids[: self.max_count]]
        else:
            raise ValueError(f"Invalid domain: {self.domain}")

    def _retrieve_description(
        self, data: pcp.Compound | pcp.Substance
    ) -> Iterable[pcp.Compound | pcp.Substance]:
        cids = [data.cid] if self.domain == "compound" else data.cids
        return [
            requests.get(
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
            ).json()
            for cid in cids
        ]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any,
    ) -> list[Document]:
        LOGGER.debug(f"Querying PubChem for {query}")
        results = self._retrieve_data(query)
        results = list(
            unique(
                results, key=lambda r: r.cid if self.domain == "compound" else r.cids
            )
        )
        descriptions = (self._retrieve_description(r) for r in results)
        title_descriptions = [
            (
                "\n".join(
                    d["Title"]
                    for desc in descs
                    for d in desc["InformationList"]["Information"]
                    if "Title" in d
                ),
                "\n".join(
                    d["Description"]
                    for desc in descs
                    for d in desc["InformationList"]["Information"]
                    if "Description" in d
                ),
            )
            for r, descs in zip(results, descriptions)
        ]
        return list(
            unique(
                (
                    Document(
                        metadata={
                            "cid": (
                                data.cid
                                if self.domain == "compound"
                                else ",".join(str(c) for c in data.cids)
                            ),
                            "sid": data.sid if self.domain == "substance" else None,
                            "source": f"https://pubchem.ncbi.nlm.nih.gov/{self.domain}/{data.cid if self.domain == 'compound' else data.sid}",
                            "title": title,
                            "molecular_formula": (
                                data.molecular_formula
                                if self.domain == "compound"
                                else None
                            ),
                            "molecular_weight": (
                                data.molecular_weight
                                if self.domain == "compound"
                                else None
                            ),
                            "synonyms": (
                                ",".join(data.synonyms[:3])
                                if self.domain == "compound"
                                else None
                            ),
                        },
                        page_content=desc,
                    )
                    for (title, desc), data in zip(title_descriptions, results)
                    if len(desc) > 20
                ),
                key=lambda doc: doc.page_content,
            )
        )


def get_pubchem_retriever(
    domain: str = "compound", max_count: int = 5
) -> BaseRetriever:
    return PubChemRetriever(domain=domain, max_count=max_count)
