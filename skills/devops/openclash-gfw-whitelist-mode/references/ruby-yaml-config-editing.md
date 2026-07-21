# Ruby YAML Config Editing for OpenClash

## Why Ruby?

OpenClash ships with Ruby as a dependency (`ruby -ryaml`). It's available on both OpenWrt and ImmortalWrt. Using Ruby for YAML manipulation is **strictly more reliable** than `sed` because:

- YAML Unicode escapes (`\U0001F3AF`) are handled correctly
- Block sequence indentation is preserved
- Array insertion at specific positions is straightforward
- No risk of corrupting the YAML structure

## Core Pattern

```bash
CONFIG=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)

ruby -ryaml -e '
  config = YAML.load_file(ARGV[0])
  
  # --- modifications ---
  
  File.open(ARGV[0], "w") { |f| YAML.dump(config, f) }
  puts "OK"
' "$CONFIG"
```

## Common Operations

### 1. Insert rules before MATCH

```ruby
match_idx = config["rules"].rindex { |r| r.include?("MATCH") }

new_rules = [
  "DOMAIN-SUFFIX,github.com,PROXY",
  "DOMAIN-SUFFIX,weixin.qq.com,\u{1F3AF}不用代理"
]

# Insert in reverse order to preserve sequence
new_rules.reverse.each do |rule|
  config["rules"].insert(match_idx, rule)
end
```

### 2. Replace MATCH target

```ruby
config["rules"].map! do |r|
  if r.include?("MATCH")
    "MATCH,\u{1F3AF}不用代理"  # 🎯不用代理
  else
    r
  end
end
```

### 3. Remove specific rules

```ruby
# Remove by content match
config["rules"].reject! { |r| r.include?("github.com") }

# Remove empty strings
config["rules"].reject! { |r| r.nil? || r.empty? }
```

### 4. List all proxy group names

```ruby
config["proxy-groups"].each { |g| puts g["name"] }
```

### 5. Add rule at specific position (e.g., right after GEOIP)

```ruby
geoip_idx = config["rules"].rindex { |r| r.include?("GEOIP") }
config["rules"].insert(geoip_idx + 1, "DOMAIN-SUFFIX,example.com,DIRECT")
```

## Unicode Handling

OpenClash uses YAML Unicode escape sequences for emoji in group names:

| Character | Ruby Escape | YAML Escape (in file) |
|-----------|-------------|----------------------|
| 🎯 | `\u{1F3AF}` | `\U0001F3AF` |
| 🐟 | `\u{1F41F}` | `\U0001F41F` |
| 🌍 | `\u{1F30D}` | `\U0001F30D` |
| 🧱 | `\u{1F9F1}` | `\U0001F9F1` |
| 🎮 | `\u{1F3AE}` | `\U0001F3AE` |

**Important**: Ruby's `YAML.dump` writes Unicode escapes in the `\u{XXXX}` format, but OpenClash uses `\UXXXXXXXX` (8-digit uppercase). When Ruby re-serializes YAML, it may change the escape format. This is usually fine — both formats are valid YAML and Clash parsers accept both. However, if you encounter issues after editing:

```ruby
# Force the specific format by writing raw string
File.open(ARGV[0], "w") do |f|
  config["rules"].each { |r| f.puts "- \"#{r}\"" }
end
```

## Complete Example: Batch Add Rules

```bash
CONFIG=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)

ruby -ryaml -e '
  config = YAML.load_file(ARGV[0])

  # Rules to add
  new_rules = [
    "DOMAIN-SUFFIX,githubusercontent.com,PROXY",
    "DOMAIN-SUFFIX,githubassets.com,PROXY",
    "DOMAIN-SUFFIX,github.io,PROXY",
    "DOMAIN-SUFFIX,githubapp.com,PROXY",
    "DOMAIN-SUFFIX,api.weixin.qq.com,\u{1F3AF}不用代理",
    "DOMAIN-SUFFIX,mp.weixin.qq.com,\u{1F3AF}不用代理",
    "DOMAIN-SUFFIX,weixin.qq.com,\u{1F3AF}不用代理"
  ]
  
  # Remove existing versions of these rules
  existing_domains = new_rules.map { |r| r.split(",")[1] }
  config["rules"].reject! { |r| existing_domains.any? { |d| r.include?(d) } }
  
  # Insert at MATCH position
  match_idx = config["rules"].rindex { |r| r.include?("MATCH") }
  new_rules.reverse.each { |r| config["rules"].insert(match_idx, r) }
  
  File.open(ARGV[0], "w") { |f| YAML.dump(config, f) }
  puts "OK: inserted #{new_rules.size} rules"
' "$CONFIG"
```

## Pitfalls

1. **`YAML.load_file` vs `safe_load`**: OpenClash config may contain aliases or custom types. Use `YAML.load_file` (not `safe_load`) to avoid parse errors.

2. **`reject!` returns `nil`**: If no elements were removed, `reject!` returns `nil`. Chain with `|| true` when using in one-liners.

3. **Ruby encoding**: OpenClash runs `ruby -E UTF-8` by convention. If you get encoding errors, add `-E UTF-8` to the shebang args.

4. **File locking**: Always close with `ensure` or a block. If the script crashes mid-write, the config file may be truncated — keep a backup.
