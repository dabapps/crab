import os
from crab import router, __version__
import shlex
import socket
import sys
from dotenv import dotenv_values
import shutil


def get_free_port():
    """Return a free port on localhost. Not 100% race-condition-safe,
    but should be fine for our purposes. https://gist.github.com/dbrgn/3979133"""
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return str(port)


def read_procfile(path):
    processes = {}
    for line in open(path):
        name, command = line.split(":", 1)
        processes[name] = shlex.split(command.strip())
    return processes


def main(command=None):

    command = command or sys.argv[1:]

    if not command or command[0] == "--version":
        print("crab v" + __version__)
        return

    # special case for the router
    if command[0] == "router":
        router.run()
        return

    # do we need to inject a free port into the environment?
    should_provide_port = False

    # start with the base environment
    env = dict(**os.environ)

    # add stuff from the envfile(s)
    envfile_paths = env.get("ENV_FILE", ".env").split(",")
    for envfile_path in envfile_paths:
        if os.path.exists(envfile_path):
            env.update(dotenv_values(envfile_path))

    # procfile handling
    if len(command) == 1:
        procfile_paths = env.get("PROC_FILE", "Procfile").split(",")
        for procfile_path in procfile_paths:
            if os.path.exists(procfile_path):
                parsed_procfile = read_procfile(procfile_path)
                if command[0] in parsed_procfile:
                    should_provide_port = command[0] == "web"
                    command = parsed_procfile[command[0]]
                break

    # add extra bin dir(s) to the PATH
    extra_bin_dirs = env.get("BIN_DIRS", "env/bin")
    env["PATH"] = ":".join(
        part for part in [extra_bin_dirs, os.getcwd(), env.get("PATH")] if part
    )

    # Provide a port to bind to if the process in a procfile app is called "web",
    # or if the command asks for one, or if explicitly specified.
    if (
        should_provide_port
        or "$PORT" in " ".join(command)
        or "CRAB_PROVIDE_PORT" in os.environ
    ):
        # provide a port in the environment and command line
        port = env.setdefault("PORT", get_free_port())
        command = [item.replace("$PORT", port) for item in command]

    if shutil.which(command[0], path=env["PATH"]) is None:
        print('Could not find "{}" in your procfile or $PATH.'.format(command[0]))
        exit(1)

    # off we go
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main()
