# Overwrite Script: Permanent MATCH Modification

## Full Example

This overwrite script (`/etc/openclash/custom/openclash_custom_overwrite.sh`) combines LinkedIn rule insertion with MATCH GFW whitelist modification:

```bash
#!/bin/sh
. /usr/share/openclash/ruby.sh
. /usr/share/openclash/log.sh
. /lib/functions.sh

LOG_OUT "Tip: Start Running Custom Overwrite Scripts..."
LOGTIME=$(echo $(date "+%Y-%m-%d %H:%M:%S"))
LOG_FILE="/tmp/openclash.log"
CONFIG_FILE="$1"

# Insert LinkedIn rule at the beginning of rules array
ruby -ryaml -rYAML -I "/usr/share/openclash" -E UTF-8 -e "
   begin
      Value = YAML.load_file('$CONFIG_FILE');
   rescue Exception => e
      puts '${LOGTIME} Error: Load File Failed - ' + e.message;
   end;
   begin
      Value['rules'].insert(0, 'DOMAIN-SUFFIX,linkedin.com,' + Value['proxy-groups'][0]['name'])
   rescue Exception => e
      puts '${LOGTIME} Error: Insert Rule Failed - ' + e.message;
   ensure
      File.open('$CONFIG_FILE','w') {|f| YAML.dump(Value, f)};
   end" 2>/dev/null >> $LOG_FILE

# GFW Whitelist Mode: unmatched traffic goes DIRECT instead of Proxy
sed -i "s/- MATCH,🐟境外网站/- MATCH,🎯不用代理/" "$CONFIG_FILE"

exit 0
```

## Inject the sed Line into Existing Script

If the script already exists with other logic:

```bash
# Adds the sed line right before exit 0
sed -i '/^exit 0/i\
# GFW Whitelist Mode: unmatched traffic goes DIRECT instead of Proxy\
sed -i "s/- MATCH,🐟境外网站/- MATCH,🎯不用代理/" "$CONFIG_FILE"' \
  /etc/openclash/custom/openclash_custom_overwrite.sh
```

## How It Works

1. OpenClash starts → reads `config.yaml` + `custom rules` → generates `Clash_*.yaml`
2. Runs `openclash_custom_overwrite.sh` with the generated config path as `$1`
3. Our `sed` command modifies the MATCH line in the already-generated file
4. Clash loads the modified config — MATCH now points to DIRECT

## Verification After Restart

```bash
/etc/init.d/openclash restart
sleep 8

# Check running config
tail -3 /etc/openclash/config/Clash_*.yaml
# Should show: MATCH,🎯不用代理

# Check logs for actual routing
tail -5 /tmp/openclash.log
# Should show non-GFW domains using DIRECT
```

## Pitfall: Strategy Group Names

The strategy group names (emojis) vary by OpenClash theme/language. Always verify first:

```bash
grep -E 'name:.*不用|name:.*DIRECT|name:.*Proxy' /etc/openclash/config/Clash_*.yaml
```

Common variants: `🎯不用代理`, `DIRECT`, `♻️ 自动直连`, `🐟境外网站`, `🐛境外网站`
