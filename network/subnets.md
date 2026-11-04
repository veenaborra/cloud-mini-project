# Subnet plan for 10.20.0.0/16

## Method
1. Sort requirements from largest to smallest: app (1,000), public (250), data (100), management (20).
2. For each, choose the smallest prefix whose usable hosts, 2^(32 - prefix) - 2, is at least the requirement.
3. Place each subnet right after the previous one, starting at 10.20.0.0. Going from largest to smallest keeps
   every subnet aligned to its own size, so no addresses are wasted between them.

## Working
| Subnet | Hosts needed | Prefix | Check | Addresses |
|---|---|---|---|---|
| app | 1,000 | /22 | 2^10 - 2 = 1,022 >= 1,000 (/23 gives only 510) | 1,024 (third octet 0 to 3) |
| public | 250 | /24 | 2^8 - 2 = 254 >= 250 (/25 gives only 126) | 256 |
| data | 100 | /25 | 2^7 - 2 = 126 >= 100 (/26 gives only 62) | 128 |
| management | 20 | /27 | 2^5 - 2 = 30 >= 20 (/28 gives only 14) | 32 |

Placement:
- app: 10.20.0.0 + 1,024 addresses -> ends at 10.20.3.255; next free 10.20.4.0
- public: 10.20.4.0 + 256 -> ends at 10.20.4.255; next free 10.20.5.0
- data: 10.20.5.0 + 128 -> ends at 10.20.5.127; next free 10.20.5.128
- management: 10.20.5.128 + 32 -> ends at 10.20.5.159; next free 10.20.5.160

Network address = first address of the block, broadcast = last, usable range = everything in between.

## Result
| Subnet | Network address | Prefix | Usable host range | Broadcast | Usable hosts |
|---|---|---|---|---|---|
| app | 10.20.0.0 | /22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1,022 |
| public | 10.20.4.0 | /24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 10.20.5.0 | /25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 10.20.5.128 | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

Free space left: 10.20.5.160 to 10.20.255.255.
Verified with Python's ipaddress module.
