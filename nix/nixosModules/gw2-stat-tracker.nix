{ pkgs
, lib
, config
, ...
}:
let
  WorkingDirectory = "/srv/gw2_stats_tracker";
  StreamlitConfig = pkgs.writeText "config.toml" ''
    [theme]
    base="dark"
    primaryColor="#AB00AB"

    [server]
    port = 14443

    [client]
    showErrorDetails = false
  '';
in
{

  options = {
    gw2-stat-tracker = {
      enable = lib.mkEnableOption "enables gw2 streamlit app";
      caddy = {
        enable = lib.mkEnableOption ''
          Enable the caddy reverse proxy for this service.
          Be sure to also set your email in caddy.service.globalConfig.
          If disabled the app is only hosted on localhost:14443.
        '';
        domainName = lib.mkOption {
          default = "";
          example = "my-domain.net";
          description = "Used as the virtualHosts for the caddy reverse proxy.";
          type = lib.types.str;
        };
      };
    };
  };

  config = lib.mkIf config.gw2-stat-tracker.enable {
    systemd.timers."gw2-stat-tracker" = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = "*-*-* 03:30:00";
        RandomizedDelaySec = "1800";
        Persistent = "true";
        Unit = "gw2-stat-tracker-restart";
      };
    };
    systemd.services = {
      "gw2-stat-tracker-restart" = {
        description = "Service for restarting the gw2 streamlit app";
        script = ''
          ${pkgs.systemd}/bin/systemctl restart gw2-stat-tracker.service
        '';
        serviceConfig = {
          Type = "oneshot";
        };
      };
      "gw2-stat-tracker" = {
        description = "Service for hosting the gw2 streamlit app";
        script = ''
          ${pkgs.coreutils}/bin/mkdir -vp ${WorkingDirectory}/.streamlit
          cp -v ${StreamlitConfig} ${WorkingDirectory}/.streamlit/${StreamlitConfig.name}
          cd ${WorkingDirectory}
          ${pkgs.nix}/bin/nix run "github:punsii/gw2_stats_tracker/master"
        '';
        wantedBy = [ "multi-user.target" ];
        requires = [ "network-online.target" ];
        after = [ "network-online.target" ];
        # serviceConfig = { };
      };
    };

    services.caddy =
      let
        domain = config.gw2-stat-tracker.caddy.domainName;
      in
      lib.mkIf config.gw2-stat-tracker.caddy.enable {
        enable = true;
        virtualHosts.${domain}.extraConfig = ''
          encode gzip
          reverse_proxy 127.0.0.1:14443
        '';
      };
    networking.firewall.allowedTCPPorts = lib.mkIf config.gw2-stat-tracker.caddy.enable [
      80
      443
    ];
  };
}






