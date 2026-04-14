# WireGuard VPN Setup on Raspberry Pi 5

WireGuard is a fast, modern VPN protocol built into the Linux kernel.
This lets you connect securely to your home network from anywhere,
reach the Investment Assistant chat UI, and integrate IoT devices.

---

## 1. Install WireGuard on the Pi

```bash
sudo apt update && sudo apt install -y wireguard wireguard-tools
```

---

## 2. Generate Server Key Pair

```bash
cd /etc/wireguard
umask 077
wg genkey | tee server_private.key | wg pubkey > server_public.key
cat server_private.key   # copy this into wg0.conf → PrivateKey
cat server_public.key    # share this with each client
```

---

## 3. Create Server Config

```bash
sudo cp /path/to/config/wireguard/wg0.conf.template /etc/wireguard/wg0.conf
sudo nano /etc/wireguard/wg0.conf
```

Fill in:
- `PrivateKey` → contents of `server_private.key`
- Each `[Peer]` `PublicKey` → the public key of that device

If your Pi uses **WiFi** instead of Ethernet, change `eth0` to `wlan0`
in the `PostUp`/`PostDown` iptables rules.

---

## 4. Enable IP Forwarding

```bash
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 5. Start & Enable WireGuard

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show    # verify it's running
```

---

## 6. Router Port Forwarding

On your home router, forward **UDP port 51820** → **Pi's LAN IP** (e.g. 192.168.1.100).

If your ISP gives you a dynamic IP, set up a **free DDNS** service
(e.g. Duck DNS: https://www.duckdns.org) and use the DDNS hostname
in your client configs.

---

## 7. Generate Client Key Pairs (one per device)

On each client device (or generate on Pi and transfer securely):

```bash
wg genkey | tee phone_private.key | wg pubkey > phone_public.key
```

Add the **public key** to the corresponding `[Peer]` block in `/etc/wireguard/wg0.conf`,
then restart: `sudo systemctl restart wg-quick@wg0`

---

## 8. Client Config

Copy `config/wireguard/client.conf.template`, fill in:
- `PrivateKey` → client's private key
- `PublicKey` → server's public key
- `Endpoint` → your DDNS hostname or public IP + `:51820`

Import the file (or generate a QR code) into the **WireGuard app**
(Android/iOS/Windows/macOS).

**Generate QR code for phone:**
```bash
sudo apt install qrencode
qrencode -t ansiutf8 < phone.conf
```

---

## 9. IoT Device Integration

For devices that support WireGuard (routers, Linux SBCs):
- Generate a key pair, add a `[Peer]` block, give it a static VPN IP (e.g. 10.8.0.10)
- Install the WireGuard client on the device
- Now your fridge, vacuum, etc. are reachable at their VPN IPs from anywhere

For devices that don't support WireGuard natively:
- Put them on a VLAN and route that VLAN through the Pi

---

## 10. Verify from Phone

1. Connect to a cellular network (not home WiFi)
2. Enable WireGuard on your phone
3. Visit `https://10.8.0.1` (Pi's VPN IP) → your Investment Assistant UI appears
4. `ping 10.8.0.1` should work

Your Investment Assistant is now accessible **only via your VPN** — from anywhere in the world.
