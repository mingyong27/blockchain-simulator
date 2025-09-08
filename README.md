
#How to run code 
| Argument         | Description                             | Default |
| ---------------- | --------------------------------------- | ------- |
| `--consensus`    | Consensus algorithm (`pow` or `hybrid`) | `pow`   |
| `--steps`        | Number of simulation steps              | `10000` |
| `--delay`        | Base network delay in ms                | `150`   |
| `--partition_at` | Time (ms) when network splits           | `None`  |
| `--heal_at`      | Time (ms) when network heals            | `None`  |
| `--nodes`        | Number of participating nodes           | `5`     |
For example:
PoW:
python3 main.py --consensus pow --steps 10000 --delay 150
Hybrid Consensus:
python3 main.py --consensus hybrid --steps 10000 --delay 150
Hybrid with Partition
python3 main.py --consensus hybrid --steps 10000 --delay 100 --partition_at 1000 --heal_at 5000
