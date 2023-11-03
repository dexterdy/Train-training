import pickle

from matplotlib import pyplot as plt

with open("300gen_initb", "rb") as file:
    results = pickle.load(file)
    resultsInsertion = results[0]
    resultsEvolutionary = results[1]
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_axes((0.2, 0.1, 0.75, 0.85))
    ax.yaxis.grid(True)
    ax.set_xticks([1, 2], ["Insertion", "Evolution"])
    ax.set_ylabel("Average passenger travel time")
    ax.violinplot(
        [resultsInsertion, resultsEvolutionary],
        showmeans=True,
        showextrema=True,
        showmedians=False,
    )

    plt.savefig("violinplot.pdf")
