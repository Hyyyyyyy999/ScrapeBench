#!/bin/bash
cd /root/scrapebench || exit 1
while pgrep -f "chain_fix\.sh" > /dev/null || pgrep -f "chain_c2\.sh" > /dev/null || pgrep -f "chain_order2\.sh" > /dev/null; do sleep 180; done
while pgrep -f "scrapebench.runner" > /dev/null; do sleep 120; done
echo "$(date '+%F %T') final: all experiments done, running report" >> logs/final.log
sleep 30
python3 -m scrapebench.runner.report --config configs/full.yaml >> logs/final.log 2>&1
python3 scripts/gen_paper_tables.py --run full >> logs/final.log 2>&1
python3 scripts/gen_paper_macros.py --run full >> logs/final.log 2>&1
git add -A && git commit -q -m "auto: final experiment results, paper tables and macros regenerated" && git push -q "$(git config --get remote.origin.url | sed 's|https://|https://x-access-token:'"$(cat /root/.scrapebench_pat)"'@|')" HEAD:main >> logs/final.log 2>&1
echo "$(date '+%F %T') final: report+tables+push done" >> logs/final.log
