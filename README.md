# H5N1-State-and-County-Simulations-and-Analysis

# County-Level Dairy Cattle Disease Spread Simulation

This repository contains code to simulate disease spread among dairy cattle populations at the **county level** using cattle movement data between counties.  
The main script, **`runsimulation_countywise.py`**, runs stochastic simulations based on county-level parameters such as number of dairy cows, number of premises, and cattle movement volumes.

---

## Model Overview

Each county is treated as a node in a temporal network, and cattle movements between counties represent edges in the snapshot of temporal network for day t with weights corresponding to the **volume of cows moved** on that day.

The county recovery period (`μ_Ci`) for a county *i* is modeled as:

\[
\mu_{C_i} = \text{round}\left( \mu_c \cdot (1 + \alpha \cdot \log(S_i)) \cdot (1 + \gamma \cdot \log(1 + P_i)) \right)
\]

where:

- **μ_c** — recovery period of a single cow
- **Sᵢ** — total number of dairy cows in county *i*  
- **Pᵢ** — total number of premises in county *i*  
- **α** — scaling parameter for number of cows  
- **γ** — scaling parameter for number of premises  

The probability of infection between two counties *u* and *v* is:

\[
\P_{uv}(t) = 1 - \exp(-\beta \cdot w_{uv}(t))
\]

where:

- **β** — transmission coefficient  
- **w_uv** — number (or volume) of cows moved between counties *u* and *v* on day **t**

---

## Usage

Run the simulation from the command line:

```bash
python runsimulation_countywise.py seed mu_c beta alpha gamma epi_start_day epi_end_day num_sim num_dairy_networks
