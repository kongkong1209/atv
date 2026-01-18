import subprocess


def run_module_stream(command, cwd=None):
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.stdout is None:
        return
    for line in iter(process.stdout.readline, ""):
        if line:
            yield line.rstrip("\n")
    process.stdout.close()
    process.wait()
