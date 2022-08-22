# CobraPlus
## Folders
- core components:
  - buildgraph: parse histories and build graphs, which will be passed to checkers for verification.
  - checker: include verifiers of a variety of workloads. These verifiers are based on z3 and MonoSAT.
  - parse: parse-related utility functions for parsing histories collected by Jepsen.

  - examples: main functions
  - exp: scripts for running experiments systematically, call the main functions in examples


## Usage
In the `cobraplus` dir, execute the following command:
```
python -m wr_range_main --sub-dir range_query_logs/12.4/automatic_mu/serializable-wrmu-c50-t40-r500-MWPK4/run15
--workload rra --checker monosat --table-count 3
```
The `sub-dir` is the directory containing the poly graph. If you want to regenerate the poly graph instead of using the existing one, you may provide `--regenerate` flag. Feel free to customize your own parameters.

Some notes for myself :failed to install monosat in conda virtual environment and I can only install it in the system interpreter. There are still many other packages like bitmap which require installing. But I insist on not polluting the system interpreter, considering that conda doesn't support inheriting global site-packages, I use virtualenv as the virtual environment tool. And install the monosat in system interpreter while keep other packages in the `venv` to minimize the effect of polluting the global interpreter. So the original conda envs are deprecated and I migrate to virtualenv.


