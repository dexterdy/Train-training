import pickle
import numpy as np
import scipy


def get_SE(data: np.ndarray):
    return np.std(data, ddof=1) / np.sqrt(np.size(data))


def do_analysis(filePath: str) -> float:
    with open(filePath, "rb") as file:
        results = pickle.load(file)
        resultsInsertion = results[0]
        resultsEvolutionary = results[1]
    SE_ins = get_SE(resultsInsertion)
    SE_evo = get_SE(resultsEvolutionary)
    SE_combined = np.sqrt(SE_ins * SE_ins + SE_evo * SE_evo)
    z = (np.mean(resultsInsertion) - np.mean(resultsEvolutionary)) / SE_combined
    p = scipy.stats.norm.sf(abs(z))
    print(
        (
            np.mean(resultsInsertion) - np.mean(resultsEvolutionary),
            1.96 * SE_combined,
            abs(z),
            p,
        )
    )
    return p


resultFiles = [
    "small_network",
    "300gen",
    "300gen_mutationb",
    "300gen_initb",
]
p_values = list(map(lambda x: do_analysis(x), resultFiles))
