#!/usr/bin/env python3
"""Get a Google Ads refresh token using the installed app flow.

Usage:
  python3 get_refresh_token.py         # looks for ../../../google-ads.yaml
  python3 get_refresh_token.py --yaml /path/to/google-ads.yaml --write

If --write is provided and the yaml exists, the script will write the
refresh_token into the yaml (requires PyYAML to preserve formatting, but
falls back to a simple key: value writer).
"""
import os
import argparse
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except Exception as e:
    print("Missing dependency: google-auth-oauthlib. Install it with:\n  pip install google-auth-oauthlib")
    raise

try:
    import yaml
except Exception:
    yaml = None


def load_yaml(path):
    if not os.path.exists(path):
        return {}
    if yaml:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    data = {}
    with open(path, "r") as f:
        for line in f:
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def write_yaml_simple(path, data):
    if yaml:
        with open(path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return
    with open(path, "w") as f:
        for k, v in data.items():
            f.write(f"{k}: {v}\n")


def main():
    parser = argparse.ArgumentParser()
    default_yaml = "google-ads.yaml"
    if not os.path.exists(default_yaml):
        default_yaml = os.path.join("..", "..", "..", "google-ads.yaml")
    parser.add_argument("--yaml", default=default_yaml,
                        help="Path to google-ads.yaml (default: local google-ads.yaml if present, otherwise ../../../google-ads.yaml)")
    parser.add_argument("--client-id", dest="client_id", help="Override client_id from yaml")
    parser.add_argument("--client-secret", dest="client_secret", help="Override client_secret from yaml")
    parser.add_argument("-w", "--write", action="store_true", help="Write the refresh_token back into the yaml")
    parser.add_argument("--port", type=int, default=8080, help="Local server port to receive the OAuth callback (default: 8080)")
    args = parser.parse_args()

    yaml_path = os.path.abspath(args.yaml)
    cfg = load_yaml(yaml_path)

    client_id = args.client_id or cfg.get("client_id")
    client_secret = args.client_secret or cfg.get("client_secret")

    if not client_id or not client_secret:
        print("client_id or client_secret not found in", yaml_path)
        client_id = input("Enter client_id: ").strip()
        client_secret = input("Enter client_secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    scopes = ["https://www.googleapis.com/auth/adwords"]

    flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes)
    creds = flow.run_local_server(port=args.port, prompt="consent")

    if not creds.refresh_token:
        print("No refresh token was returned. Ensure you grant offline access and this is the first time you authorize this client.")
        if args.write:
            print("Refresh token not written because authorization was not completed.")
            sys.exit(1)
    print("REFRESH_TOKEN:", creds.refresh_token)

    if args.write:
        if not os.path.exists(yaml_path):
            print("Cannot write: yaml path does not exist:", yaml_path)
            sys.exit(1)
        cfg["refresh_token"] = creds.refresh_token
        write_yaml_simple(yaml_path, cfg)
        print("Wrote refresh_token to", yaml_path)


if __name__ == "__main__":
    main()
