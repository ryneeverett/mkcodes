with import <nixpkgs> {};
let
  mkcodesEnv = poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    # editablePackageSources = {
      # mkcodes = ./mkcodes;
    # };
  };
in
  pkgs.mkShell {
    buildInputs = [
      pkgs.poetry
      mkcodesEnv
    ];
  }
