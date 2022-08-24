# Viper
This is the root directory of a research project, Viper. [Viper: A Fast Snapshot Isolation Checker]() is a research paper studying checking snapshot isolation of black-box databases. It consists of two components:
* [Viper](https://github.com/Khoury-srg/Viper): checks snapshot isolation of a set of transactions (called a _history_)
* [Viper bench](https://github.com/Khoury-srg/ViperBench): database clients that interact with a black-box database and generate histories

If you want to generate new histories, see [Viper bench](https://github.com/Khoury-srg/ViperBench).

## How to run?
### Using Docker (Recommended)
We prepared a docker file for easier reproduction in the `cobraplus_backend/cobraplus/docker` folder. 

#### Pre-requisites for use
- Ubuntu 20.04
- docker 
- VNC Viewer: Elle requires GUI and hence we run a VNC server in the docker container.

#### Step 1: Download artifacts and set environment variables

Download `Viper`:
```bash
git clone https://github.com/Khoury-srg/Viper.git
cd Viper
export VIPER_HOME=<YOUR_VIPER_PATH>
```

Prepare input data:
Download `history.tgz` from [Google Drive](https://drive.google.com/file/d/1y0QttN1lWkHZ_emkTkvsIhxmKRYBKqKf/view?usp=sharing) to `$VIPER_HOME`.
You may download it manually or using following statements:
```bash
pip install gdown
gdown https://drive.google.com/uc?id=1y0QttN1lWkHZ_emkTkvsIhxmKRYBKqKf
move history.tgz $VIPER_HOME/
```


```bash
cd $VIPER_HOME
tar xzvf history.tgz
```

#### Step 2: Configure the log path
Modify the `config.yaml` as follows:
```bash
PREFIX: &prefix "/Viper/history_data"
LOG_DIR: "/Viper/history_data/logs"
GRAPH_DIR: "/Viper/history_data/graphs"
ANALYSIS_DIR: "/Viper/history_data/Analysis_logs"
```

#### Step 3: Build the docker image and start the container 

    $ cd $VIPER_HOME/
    $ sudo docker pull windkl/viper:latest 

If you want to build from the Dockerfile:

    $ sudo docker build -t windkl/viper:latest . --no-cache -f cobraplus_backend/cobraplus/docker/Dockerfile

Then launch a container. `VNC_PASSWORD` is the password you will use to connect to the VNC server later.
```bash
sudo docker run -d --name viper -p 6080:80 -p 5900:5900 -e VNC_PASSWORD=viper321 -v $VIPER_HOME:/Viper -v /dev/shm:/dev/shm  windkl/viper:latest 
```


#### Step 4: Connect to the VNC server & open the terminal
1. Open VNC Viewer, configure the IP address and enter the VNC_PASSWORD above to connect to the docker contaienr. Make sure that the TCP port 5900 is open on the Ubuntu machine.
2. Open System tools -> LXTerminal.
3. ```bash
    cd /Viper 
    export VIPER_HOME=$PWD
    ```

#### Step 5: Run the experiments

Run the python scripts in the folder `./cobraplus_backend/cobraplus/ae`. Each script corresponds to a figure in the paper and will generate a txt file to store the results, e.g. `run_fig8.sh` will generate `fig8.txt` in `VIPER_HOME`. If the result of a particular algorithms on a benchmark does not show in the txt file, it represents that the algorithms times out.

```bash
cd $VIPER_HOME
./cobraplus_backend/cobraplus/ae/run_fig8.sh
./cobraplus_backend/cobraplus/ae/run_fig9.sh
./cobraplus_backend/cobraplus/ae/run_fig10.sh
./cobraplus_backend/cobraplus/ae/run_fig11.sh
./cobraplus_backend/cobraplus/ae/run_fig12.sh
./cobraplus_backend/cobraplus/ae/run_BE19.sh 
```

`dbcop-BE19`  may encounter out of memory error as reported in the paper and hence the `run_BE19.sh` may not exit normally. The checking results of `dbcop` is stored in `$VIPER_HOME/BE19_output`. The results of `dbcop-BE19` and `dbcop-SAT` are outputed as a json file in the `$VIPER_HOME/BE19_output/XXX/output_dir` and `$VIPER_HOME/BE19_output/XXX/output_sat_dir` folder respectively, where `XXX` is the history name. 
You may check the value of `sat` and `duration` in those json files to see whether the give history is satifiable and how long it takes to do the checking.

##### Run `Viper` for a single history
To run `Viper` for a single history instead of using the provided scripts:
```bash
python3.8 -m cobraplus_backend.cobraplus.main_allcases --config_file cobraplus_backend/cobraplus/config.yaml --algo 6 --sub_dir cheng/normal-Cheng-5000txns-8oppertxn-threads24-I0-D0-R50-U50-RANGEE0-2022-08-19-15-42-40/jepsen --perf_file ./test_perf.txt --exp_name test_run
```

`--sub_dir` is the relative path of the log folder to the `JEPSEN_LOG_DIR` folder. `--perf_file` specifies which file you want to store the results in and `exp_name` is the name of this run.


If you generate histories using `ViperBench` or `Jepsen` by yourself, you need to organzie the 
file hierarchy as follows:
create `PREFIX`, `JEPSEN_LOG_DIR` folders as those in `config.yaml` if not exists and make sure `JEPSEN_LOG_DIR` is a subfolder of `PREFIX`. And then store your history logs in `JEPSEN_LOG_DIR`. 

### Without using Docker
#### Pre-requisites for use
- ubuntu20.04 with GUI: GUI is only needed by `elle`.
- python3.8, python3-setuptools python3-pip
- jdk11: jdk11 is only needed by `elle`
- cmake
- g++
- libgmp 
- zlib 
- libclang-dev
- Rust & cargo: only needed by a history translator for `dbcop`, which translates our history format to `dbcop`'s history format.

You may install the most of them by executing:

    $ sudo apt-get update && sudo apt-get install -y libgmp-dev cmake g++ zlib1g-dev openjdk-11-jdk libclang-dev python3.8 python3-setuptools python3-pip

Install Rust:

    $ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh


#### Step 1: Download Viper and install dependencies
Same as the Step 1 above.

#### Step 2: Install dependencies
##### install [MonoSAT](https://github.com/sambayless/monosat)
```bash
cd $VIPER_HOME/resources/monosat
cmake -DPYTHON=ON .
make
sudo make install
```

##### install [z3](https://github.com/Z3Prover/z3)
```bash
$VIPER_HOME/resources/z3
python scripts/mk_make.py
cd build
make
sudo make install
```

##### install Python packages
```bash
cd cobraplus_backend/cobraplus/docker
pip3 install --no-cache-dir -r requirements.txt
```

##### build [elle-cli](https://github.com/ligurio/elle-cli)

```bash
cd $VIPER_HOME/resources/
tar xzvf elle.tgz
cd elle-cli-0.1.3
lein deps
lein uberjar
```

##### install [BE19](https://gitlab.math.univ-paris-diderot.fr/ranadeep/dbcop)
```bash
cd $VIPER_HOME/resources/
tar xzvf BE19_translator.tgz
cd BE19_translator
cargo build

cd $VIPER_HOME/resources/dbcop
cargo build
```

#### Step 3: Configure logs path

Modify the `cobraplus_backend/cobraplus/config.yaml` as follows. Note that replace <VIPER_HOME> with your path.
```bash
PREFIX: &prefix "<VIPER_HOME>/jepsen_data"
JEPSEN_LOG_DIR: "<VIPER_HOME>/jepsen_data/jepsen_logs"
GRAPH_DIR: "<VIPER_HOME>/jepsen_data/graphs"
ANALYSIS_DIR: "<VIPER_HOME>/jepsen_data/Analysis_logs"
```

#### Step 4: Specify the path of `dbcop` and run experiments
Note that the paths of `dbcop` and `translator` need to be specified in `run_BE19.sh` by commenting out the code snippet of `using docker` and uncommenting the snippet of `w/o docker`.

#### Step 5: Run experiments
Then you may run the experiments the same as the Step 5 in the section of using docker.
