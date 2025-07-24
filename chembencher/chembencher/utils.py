import json
import logging
import os
from concurrent.futures.thread import ThreadPoolExecutor

from chembench.task import Task
from langchain_core.runnables import Runnable
from tqdm import tqdm

from chembencher.collect_scores import combine_scores_for_all_models
from chembencher.model_wrapper import ModelWrapper

LOGGER = logging.getLogger(__name__)

ALL_CATEGORIES = [
    "gfk",
    "number_nmr_peaks",
    "point_group",
    # "oxidation_states",
    "oup",
    "reactive_groups",
    "toxicology",
    "LMU_tox",
    "tox_pharma",
    "tox_wwu",
    "dai",
    "pictograms",
    "h_statement",
    "materials_compatibility",
    "chem_chem_comp",
    # "electron_counts",
    "organic_reactivity",
    "polymer_chemistry",
    "stolaf",
    "sci_lab_safety_test",
    "chemical_safety_mcq_exam",
    "analytical_chemistry",
    "periodic_table",
    "ac_faessler_tum",
    "pum_tum",
    "biomolecular",
    "xray",
    "materials_synthesis",
    "func_mats_and_nanomats",
    "molsim",
    "smiles_to_name",
    "name_to_smiles",
    "preference",
]


def benchmark(chain: Runnable):
    LOGGER.info("Benchmarking")
    model = ModelWrapper(chain)
    for category in tqdm(ALL_CATEGORIES):
        LOGGER.info(f"Processing category {category}")
        tasks = [
            (root, file)
            for root, dirs, files in os.walk(f"data/{category}/")
            for file in files
            if file.endswith(".json")
        ]
        # for root, file in tqdm(tasks):
        #     process_task(root, file, model)
        with ThreadPoolExecutor() as executor:
            executor.map(lambda x: process_task(x[0], x[1], model), tasks)
    combine_scores_for_all_models("reports/iaichemllm/", "summary.json", "data/")


def process_task(root: str, file: str, model: ModelWrapper):
    LOGGER.info(f"Processing task {root}{file}")
    with open(os.path.join(root, file)) as f:
        uuid = json.load(f)["uuid"]
    result_file = f"reports/iaichemllm/{uuid}/{file}"
    if os.path.exists(result_file):
        LOGGER.debug(f"Skipping {result_file}")
        return

    task = Task.from_json(os.path.join(root, file))
    report = model.run_task(task)

    LOGGER.debug(f"Writing report to {result_file}")
    os.makedirs(f"reports/iaichemllm/{uuid}", exist_ok=True)
    with open(result_file, "w") as f:
        json.dump([report.model_dump()], f)
