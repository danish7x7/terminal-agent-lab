```bash
mkdir -p /output

while read package current_version; do
    json_file="/api/responses/${package}.json"
    src_file="/src/${package}.c"
    out_file="/output/${package}.c"

    # Extract latest_version field from JSON
    latest_version=$(grep -o '"latest_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$json_file" | grep -o '[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*')

    # Compare semver: split into MAJOR MINOR PATCH
    IFS='.' read -r cur_maj cur_min cur_pat <<< "$current_version"
    IFS='.' read -r lat_maj lat_min lat_pat <<< "$latest_version"

    newer=0
    if [ "$lat_maj" -gt "$cur_maj" ]; then
        newer=1
    elif [ "$lat_maj" -eq "$cur_maj" ] && [ "$lat_min" -gt "$cur_min" ]; then
        newer=1
    elif [ "$lat_maj" -eq "$cur_maj" ] && [ "$lat_min" -eq "$cur_min" ] && [ "$lat_pat" -gt "$cur_pat" ]; then
        newer=1
    fi

    if [ "$newer" -eq 1 ]; then
        # Extract patch field value (the escaped string between "patch": " and the closing ")
        patch_escaped=$(python3 -c "
import json, sys
with open('$json_file') as f:
    data = json.load(f)
print(data['patch'], end='')
")
        cp "$src_file" "$out_file"
        echo "$patch_escaped" | patch "$out_file"
    else
        cp "$src_file" "$out_file"
    fi
done < /data/packages.txt
```