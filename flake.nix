{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs =
    {
      self,
      nixpkgs,
      poetry2nix,
    }:
    let
      supportedSystems = [
        "x86_64-linux"
        "x86_64-darwin"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgs' = forAllSystems (system: nixpkgs.legacyPackages.${system});
      poetry2nix' = forAllSystems (system: poetry2nix.lib.mkPoetry2Nix { pkgs = nixpkgs'.${system}; });

      mkPoetryProject = { pkgs, overrides }: {
        projectDir = self;
        python = pkgs.python311;
        overrides = overrides.withDefaults (
          final: prev: {
            mypy = prev.mypy.override {
              preferWheel = true;
            };
            numpy = prev.numpy.override {
              preferWheel = true;
            };
            objprint = final.addBuildSystem "setuptools" prev.objprint;
            opencv-python = prev.opencv-python.override {
              preferWheel = true;
            };
            pye3d = prev.pye3d.overridePythonAttrs (prevAttrs: {
              nativeBuildInputs = prevAttrs.nativeBuildInputs or [] ++ [
                final.setuptools
                final.cmake
                final.cython
              ];

              buildInputs = prevAttrs.buildInputs or [] ++ [
                pkgs.eigen
                final.scikit-build
              ];

              postPatch = ''
                sed -i "2i version = ${prevAttrs.version}" setup.cfg
              '';

              dontUseCmakeConfigure = true;
            });
            viztracer = final.addBuildSystem "setuptools" prev.viztracer;
          }
        );
      };
    in
    {
      formatter = forAllSystems (system: nixpkgs'.${system}.nixfmt-rfc-style);

      packages = forAllSystems (
        system:
        let
          inherit (poetry2nix'.${system}) mkPoetryApplication overrides;
          pkgs = nixpkgs'.${system};
        in
        {
          default = mkPoetryApplication (mkPoetryProject { inherit overrides pkgs; });
        }
      );

      devShells = forAllSystems (
        system:
        let
          inherit (poetry2nix'.${system}) mkPoetryEnv overrides;
          pkgs = nixpkgs'.${system};
        in
        {
          default = pkgs.mkShellNoCC {
            shellHook = ''
              echo -e "\033[0;36m:: Welcome to the EyeTrackVR Backend!\033[0m"
              echo -e "\033[0;36m:: Run \"python -m eyetrackvr_backend.main\" to start the backend\033[0m"
            '';
            packages = with pkgs; [
              (mkPoetryEnv (mkPoetryProject { inherit overrides pkgs; }))
              binutils
              poetry
            ];
          };
        }
      );
    };
}
