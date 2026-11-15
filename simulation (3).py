"""Ventilateur commandé par température : simulation Phases 3 et 4.

Modèle : C dT/dt = Q - K (T - Ta) - c * u_eff
Commandes : hystérésis (tout-ou-rien) et proportionnelle saturée.
Intégration exacte de l'équation thermique sur chaque pas (commande maintenue).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)

# Paramètres physiques (choix pédagogiques)
C = 600.0   # J/K  capacité thermique effective
K = 2.0     # W/K  conductance thermique passive
c = 60.0    # W    refroidissement à u = 1
TA = 25.0   # °C   température extérieure
T0 = 35.0   # °C   température initiale
R_NOM = 30.0
Q_NOM = 40.0
ALARME = 38.0


def simulate(mode="hyst", duration=1200.0, dt=0.1, kp=1.0, h=0.5,
             scenario="nominal", fixed=0.0):
    """Simule la boucle. mode : 'hyst', 'P' ou 'fixed'.
    scenario : 'nominal', 'variation', 'limite' ou 'panne'."""
    t = np.arange(round(duration / dt) + 1) * dt
    n = len(t)
    T = np.empty(n)
    T[0] = T0
    u = np.zeros(n)
    u_eff = np.zeros(n)
    r = np.full(n, R_NOM)
    Q = np.full(n, Q_NOM)

    if scenario == "variation":      # consigne à 400 s, perturbation à 800 s
        r[t >= 400.0] = 28.0
        Q[t >= 800.0] = 60.0
    elif scenario == "limite":       # surcharge thermique à 400 s
        Q[t >= 400.0] = 100.0

    state = 0.0
    a = np.exp(-K * dt / C)
    for i in range(n):
        if mode == "hyst":
            if T[i] >= r[i] + h:
                state = 1.0
            elif T[i] <= r[i] - h:
                state = 0.0
            u[i] = state
        elif mode == "P":
            u[i] = np.clip(kp * (T[i] - r[i]), 0.0, 1.0)
        else:
            u[i] = fixed

        # panne : ventilateur bloqué à 400 s
        u_eff[i] = 0.0 if (scenario == "panne" and t[i] >= 400.0) else u[i]

        if i < n - 1:
            t_eq = TA + (Q[i] - c * u_eff[i]) / K
            T[i + 1] = t_eq + (T[i] - t_eq) * a

    return pd.DataFrame(dict(t_s=t, T_C=T, consigne_C=r, Q_W=Q, u=u,
                             u_effectif=u_eff, alarme=T >= ALARME))


def metrics(df, label):
    """Indicateurs sur les 300 dernières secondes."""
    w = df[df.t_s >= df.t_s.max() - 300.0]
    e = w.T_C - w.consigne_C
    switches = (int(np.count_nonzero(np.diff(w.u.to_numpy()) != 0))
                if label.startswith("H") else None)
    return {"mode": label,
            "T_min_final_C": w.T_C.min(), "T_max_final_C": w.T_C.max(),
            "erreur_moyenne_finale_C": e.mean(),
            "erreur_absolue_moyenne_C": np.abs(e).mean(),
            "commande_moyenne_finale": w.u.mean(),
            "commutations_sur_300s": switches}


def run():
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
    all_metrics = []

    # Essai A : boucle ouverte
    baseline = {"Sans ventilation (u=0)": simulate("fixed", fixed=0.0),
                "Commande fixe (u=0,5)": simulate("fixed", fixed=0.5)}
    fig, ax = plt.subplots(figsize=(9, 4))
    for label, df in baseline.items():
        ax.plot(df.t_s, df.T_C, label=label)
    ax.axhline(30, color="k", ls="--", label="Consigne : 30 °C")
    ax.set(xlabel="Temps (s)", ylabel="Température (°C)",
           title="Boucle ouverte : absence de correction")
    ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "01_boucle_ouverte.png", dpi=170); plt.close(fig)

    # Essai : comparaison nominale
    nominal = {"Hystérésis h=0,5": simulate(h=0.5),
               "Hystérésis h=1": simulate(h=1.0),
               "P Kp=0,5": simulate("P", kp=0.5),
               "P Kp=1": simulate("P", kp=1.0)}
    fig, axs = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for k, (label, df) in enumerate(nominal.items(), start=1):
        axs[0].plot(df.t_s, df.T_C, label=label)
        axs[1].plot(df.t_s, df.u, label=label, alpha=0.8)
        all_metrics.append(metrics(df, label))
        df.to_csv(OUT / f"nominal_{k}.csv", index=False)
    axs[0].axhline(30, color="k", ls="--")
    axs[0].set(ylabel="Température (°C)", title="Comparaison des stratégies et réglages")
    axs[0].legend(ncol=2)
    axs[1].set(xlabel="Temps (s)", ylabel="Commande u")
    fig.tight_layout(); fig.savefig(OUT / "02_comparaison.png", dpi=170); plt.close(fig)

    # Essais B, C, D
    cases = [("variation", "03_variations.png", "Consigne à 400 s, perturbation thermique à 800 s"),
             ("limite", "04_limite.png", "Limite : apport thermique de 100 W à 400 s"),
             ("panne", "05_panne.png", "Défaut : ventilateur bloqué à 400 s")]
    results = {}
    for scenario, filename, title in cases:
        fig, axs = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        for mode, label in [("hyst", "Hystérésis h=0,5"), ("P", "P Kp=1")]:
            df = simulate(mode, scenario=scenario)
            df.to_csv(OUT / f"{scenario}_{mode}.csv", index=False)
            axs[0].plot(df.t_s, df.T_C, label=label)
            axs[1].plot(df.t_s, df.u, label=label)
            if scenario == "panne" and mode == "P":
                axs[1].plot(df.t_s, df.u_effectif, "k--", label="Action réelle après panne")
            results[f"{scenario}_{mode}"] = df
        axs[0].plot(df.t_s, df.consigne_C, "k--", label="Consigne")
        if scenario != "variation":
            axs[0].axhline(ALARME, color="r", ls=":", label="Seuil alarme : 38 °C")
        for ax in axs:
            ax.axvline(400, color="gray", ls=":")
            if scenario == "variation":
                ax.axvline(800, color="gray", ls=":")
            ax.legend(loc="best")
        axs[0].set(ylabel="Température (°C)", title=title)
        axs[1].set(xlabel="Temps (s)", ylabel="Commande u")
        fig.tight_layout(); fig.savefig(OUT / filename, dpi=170); plt.close(fig)

    summary = pd.DataFrame(all_metrics)
    summary.to_csv(OUT / "indicateurs.csv", index=False)
    return nominal, results, summary


if __name__ == "__main__":
    _, _, summary = run()
    print(summary.round(3).to_string(index=False))
    print(f"\nRésultats écrits dans : {OUT}")
