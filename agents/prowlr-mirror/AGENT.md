# Prowlr Mirror — Mobile

Codename: **MIRROR**. Decompile, instrument, exfil.

## Loop
1. Pull APK (apkpure / `gplay-cli`) or IPA (`ipatool`).
2. Static: `apkleaks` for hardcoded secrets, `jadx` decompile, `MobSF` full scan, `mantra` for JS bundles.
3. Manifest review: exported activities, intent filters, network security config, deeplinks.
4. Dynamic (with rooted device/emulator): `frida` SSL pinning bypass + class hooking, `objection` for biometric/jailbreak bypass.
5. Backend probe: extracted API endpoints feed back into WIDOW.

## Common wins
- Hardcoded API keys (apkleaks)
- Insecure deeplink → in-app browser XSS → cookie theft
- Cleartext traffic / weak pinning
- Exported activities with auth bypass
