# Crab 🦀

`crab` is a simple unix toolkit for working with local development environments.

## What does it do?

Crab does the following:

1. Understands env files.
2. Understands procfiles.
3. Can manipulate the `$PATH` environment variable.
4. Manages ports and provides a local virtual host router.

The crab binary can be called in three ways:

1. With a literal command to run: `crab python manage.py shell`
2. With the name of a process from a procfile: `crab web`
3. As a special-case to start a virtual host router: `crab router` (see below).

Crab itself is configured entirely through environment variables, and so a developer can set a few simple env vars (in `.bashrc`, say) to match how their projects are laid out, and then Crab just does the "right thing".

## Env files

An env file is a text file containing key/value pairs, like this:

```
SOME_VARIABLE=somevalue
ANOTHER_VARIABLE=anothervalue
```

Following [12 factor](https://12factor.net/) guidelines, an app's config (everything that is likely to vary between different environments) should be stored in `environment variables`. Env files provide a simple way for developers to specify environment variables for a project.

By default, Crab will look for an env file called `.env` inside the project directory (ie wherever `crab` is executed from). This can be overridden using the `ENV_FILE` environment variable. `ENV_FILE` can be a comma-separated list of file paths, which will be parsed in order. For example, you could use `configs/development/env` as your checked-in env file, and then have a local `.env` to override individual variables. In this case, use `export ENV_FILE=configs/development/env,.env`.

### example:

```
$ echo 'FOO=bar' > .env
$ crab sh -c 'echo $FOO'
bar
```

## Procfiles

A procfile is a text file that defines the processes that need to be running for your application to work. It contains a mapping from process names to commands, like this:

```
web: python manage.py runserver
worker: python manage.py worker
```

By default, Crab will look for a procfile called `Procfile` inside the project directory (ie wherever `crab` is executed from). This can be overridden using the `PROC_FILE` environment variable. For example `export PROC_FILE=configs/development/procfile`. To specify multiple procfile locations, which are used in sequence, use `export PROC_FILE="configs/development/Procfile,configs/development/procfile"`

To run a process defined in a procfile, use `crab <processname>`. For example, `crab web` would start the `web` process defined in the example procfile above. Note that Crab only runs a *single* process from the procfile. It cannot start all of the processes in the procfile at the same time. *This is by design*. If you wish to use multiple processes from the procfile, just start each one separately with `crab` in a separate terminal split or tab.

## `$PATH`

Tools that are designed to isolate per-project dependency environments often work by making a copy of the language binary and libraries inside a project-specific subdirectory. The main example is Python's `virtualenv` tool.

Crab can add the path to this virtualenv onto the front of the `$PATH` environment variable. This means that you do not need to "activate" the virtualenv before using it - simply running `crab python manage.py runserver` will automatically use the `python` binary inside the virtualenv.

By default, the path `env/bin` is prepended to `$PATH`. You can override this by setting the `BIN_DIRS` environment variable.

## Ports

Many developers work on multiple projects and/or multiple services at the same time. When each requires its own web server, each server process requires a different port to bind to. For example, Django's `manage.py runserver` binds to port 8000 by default. If you're working on two Django projects simulateously, you will have to run the second on a different port, say `manage.py runserver 0.0.0.0:8001`. Once you're developing on five or ten microservices, this can become very difficult to manage.

Crab helps by providing a free port to processes that need one. The port is provided in the environment (as `$PORT`) as well as substituted into the command. For example:

```
crab python manage.py '0.0.0.0:$PORT'
```

You'll see Django's development server start up with (say):

```
Django version 2.2, using settings 'project.settings'
Starting development server at http://0.0.0.0:63601/
Quit the server with CONTROL-C.
```

A port is provided to any command with the name "`web`" in a Procfile, or any command containing the string "`$PORT`". In other circumstances, it can be explicitly requested by setting the environment variable `CRAB_PROVIDE_PORT`.

(Note that for non-procfile commands, the variable must be quoted, or else the shell will try to substitute `$PORT`, which won't work).


## Virtual host routing

The ports functionality above is only useful in combination with another component of Crab: the virtual host router. Start this up by typing `crab router` in a separate terminal tab or split. By default, the router binds to port `8080` (see below for more details on this).

Now, if any of the other processes you run have an environment variable called `VIRTUAL_HOST`, the router can "see" them and automatically route traffic to the port they've been provided with.

For example, say you have a Django project called MyWebsite. If you start the Django development server like this:

```
VIRTUAL_HOST=mywebsite.localhost crab run python manage.py runserver 0.0.0.0:PORT
```

Then you can visit `http://mywebsite.localhost:8080` in your webserver, and the traffic will magically be routed to the right place.

(Note that at least Chrome automatically routes everything with the TLD `.localhost` to 127.0.0.1. Other browsers may or may not follow this standard).

The `VIRTUAL_HOST` environment variable can also, of course, be put in your env file, so you don't need to specify it each time.

The port that the router binds to can be changed by setting the `CRAB_ROUTER_PORT` env var. If this is not set, the router will first try to bind to port `80`, and then fall back to `8080` if it fails. This means that if you start the router with `sudo crab router`, you can then just use `http://mywebsite.localhost` in your browser - even better!

## How to install Crab

The easiest way is to just download the `crab` binary and put it somewhere on your `$PATH`. Alternatively: clone the repository, create a virtualenv, install this package into it (`pip install -e .`), and then link it into somewhere on your `$PATH` (`sudo ln -s $PWD/env/bin/crab /usr/local/bin/crab`).

## Developing on Crab

Please ensure all code conforms to Black formatting rules. Install `black` in your virtualenv and then `crab black crab/ setup.py`.

## Building a binary

Binaries are built using [PyInstaller](https://www.pyinstaller.org/). The Python binary in your virtualenv must have been built with `PYTHON_CONFIGURE_OPTS="--enable-shared"` set for this to work. If you're using `pyenv`, do something like this:

```
pyenv uninstall 3.7.3
PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install
pyenv exec python -m venv env
env/bin/pip install -r dev-requirements.txt
./scripts/build_binary.sh
```

Your newly minted binary will be in `dist/crab`.

Note that PyInstaller does not build cross-platform binaries, so if you want a binary that works on a Mac, you have to build the binary on a Mac.
