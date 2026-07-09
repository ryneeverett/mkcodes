{ pkgs ? import <nixpkgs> {},
  pyproject-nix ? import (builtins.fetchGit {
    url = "https://github.com/pyproject-nix/pyproject.nix.git";
  }) {
    inherit (pkgs) lib;
  },
}:
let
  project = pyproject-nix.lib.project.loadPyproject {
    projectRoot = ./.;
  };
  python = let
    packageOverrides = self: super: {
      mkcodes = self.mkPythonEditablePackage (pyproject-nix.lib.renderers.mkPythonEditablePackage {
        inherit project python;
      });
    };
  in pkgs.python3.override {
    inherit packageOverrides;
    self = python;
  };
  pythonEnv = python.withPackages (project.renderers.withPackages {
    inherit python;
    extraPackages = ps: [
      ps.mkcodes
    ];
    extras = [ "markdown" ];
  });
in
  pkgs.mkShell {
    buildInputs = [
      pythonEnv
    ];
  }
