#!/bin/bash
# Simple log watcher script - no pipeline changes needed

echo "Football Bot Log Watcher"
echo "Press Ctrl+C to exit"
echo "========================"

# Watch both step6 and step7 logs
echo "Watching step6 and step7 logs..."
tail -f /root/CascadeProjects/Football_bot/step6/step6_matches.log \
       /root/CascadeProjects/Football_bot/step7/step7_matches.log
