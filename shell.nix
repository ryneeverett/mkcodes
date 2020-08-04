let
  pkgs = import <nixpkgs> {};
  testDependencies = [
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.markdown
  ];
  mkcodes = pkgs.python3Packages.buildPythonPackage {
    pname = "mkcodes";
    version = "master";
    src = ./.;

    propagatedBuildInputs = [
      pkgs.python3Packages.click
    ];
    checkInputs = testDependencies;

    # FIXME
    doCheck = false;
  };
in
  pkgs.mkShell {
    buildInputs = [
      mkcodes
    ] ++ testDependencies;
  }
