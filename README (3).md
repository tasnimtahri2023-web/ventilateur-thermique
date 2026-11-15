# Ventilateur commandé par température

Simulation Python d'une enceinte thermique refroidie par un ventilateur, avec comparaison
d'une commande à **hystérésis** et d'une commande **proportionnelle saturée**.

Projet ENET'Com – 1GII1 – Tasnim Tahri, Islem Berrachd, Eya Ben Taher
Encadrante : Dr.-Ing. Ferdaous Masmoudi

> Étude virtuelle : les paramètres sont des choix pédagogiques, pas des mesures.
> Les conclusions valent pour le modèle, pas pour un prototype réel.

## Modèle

```
C dT/dt = Q - K (T - Ta) - c·u        u ∈ [0, 1]
```

| Paramètre | Valeur | Signification |
|-----------|--------|---------------|
| C  | 600 J/K | capacité thermique effective |
| K  | 2 W/K   | conductance thermique passive |
| c  | 60 W    | refroidissement à u = 1 |
| Ta | 25 °C   | température extérieure |
| Q  | 40 W    | source interne nominale |
| r  | 30 °C   | consigne nominale |

Constante de temps : τ = C/K = 300 s. Commande d'équilibre nominale : u* = 0,5.

## Commandes

- **Hystérésis** : u = 1 si T ≥ r + h, u = 0 si T ≤ r − h, sinon on garde l'état précédent.
- **P saturée** : u = sat[Kp (T − r), 0, 1] (erreur statique = (Q − K(r − Ta)) / (K + c·Kp)).

## Scénarios

| Essai | Description |
|-------|-------------|
| A | Boucle ouverte (u = 0 et u = 0,5) |
| Nominal | Hystérésis h = 0,5 / 1 et P Kp = 0,5 / 1 |
| B | Consigne 30 → 28 °C à 400 s, Q 40 → 60 W à 800 s |
| C | Surcharge Q = 100 W à 400 s (saturation) |
| D | Ventilateur bloqué à 400 s (u_eff = 0) |

## Utilisation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python simulation.py
```

Les figures (`.png`), les courbes (`.csv`) et `indicateurs.csv` sont écrits dans `results/`.

## Méthode numérique

Pas de 0,1 s ; commande maintenue entre deux instants ; intégration exacte :
`T[n+1] = Teq + (T[n] − Teq)·exp(−K·Δt/C)`, avec `Teq = Ta + (Q − c·u_eff)/K`.
Indicateurs calculés sur les 300 dernières secondes.

## Limites

Le ventilateur est supposé instantané, le capteur idéal, la température uniforme.
Le terme `c·u` ne doit pas être extrapolé sous Ta. Un modèle plus physique serait
`C dT/dt = Q − (K + Kv·u)(T − Ta)`.

## Licence

MIT (à adapter).
