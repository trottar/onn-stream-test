$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "audit_repo_checkpoint.py"
python $PythonScript @args
exit $LASTEXITCODE
