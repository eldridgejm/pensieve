with import <nixpkgs> {};
with python38Packages;

mkShell {
  venvDir = "env";
  buildInputs = [ venvShellHook ];
  postShellHook = ''
    export IN_NIX_SHELL=1
    ./env/bin/pip install -e .
    pip install behave ipython pytest black
  '';
}
