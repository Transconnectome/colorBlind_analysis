#!/bin/bash
# clean_slurm_logs.sh
# Clean up old SLURM log files
# Usage: bash clean_slurm_logs.sh

echo "=========================================="
echo "SLURM Log Cleanup"
echo "=========================================="
echo ""

# Count log files in working directory (old location)
OLD_LOGS=$(ls slurm-*.out 2>/dev/null | wc -l)
if [ $OLD_LOGS -gt 0 ]; then
    echo "Found $OLD_LOGS old log files in working directory:"
    ls -lh slurm-*.out slurm-*.err 2>/dev/null | head -5
    echo ""
    read -p "Move old logs to slurm_logs/ folder? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p slurm_logs
        mv slurm-*.out slurm-*.err slurm_logs/ 2>/dev/null
        echo "✓ Moved old logs to slurm_logs/"
    fi
else
    echo "No old log files found in working directory"
fi

echo ""

# Count log files in slurm_logs directory
if [ -d "slurm_logs" ]; then
    NEW_LOGS=$(ls slurm_logs/*.out 2>/dev/null | wc -l)
    if [ $NEW_LOGS -gt 0 ]; then
        echo "Current logs in slurm_logs/: $NEW_LOGS files"

        # Show size
        TOTAL_SIZE=$(du -sh slurm_logs 2>/dev/null | awk '{print $1}')
        echo "Total size: $TOTAL_SIZE"
        echo ""

        echo "Options:"
        echo "  1. Keep all logs"
        echo "  2. Archive logs to slurm_logs_archive.tar.gz and delete"
        echo "  3. Delete all logs"
        echo ""
        read -p "Choose option [1/2/3]: " -n 1 -r
        echo

        if [[ $REPLY == "2" ]]; then
            tar -czf slurm_logs_archive_$(date +%Y%m%d_%H%M%S).tar.gz slurm_logs/
            rm -rf slurm_logs/*
            echo "✓ Archived and cleaned slurm_logs/"
        elif [[ $REPLY == "3" ]]; then
            rm -rf slurm_logs/*
            echo "✓ Deleted all logs from slurm_logs/"
        else
            echo "✓ Keeping all logs"
        fi
    else
        echo "slurm_logs/ directory is empty"
    fi
else
    echo "slurm_logs/ directory does not exist"
fi

echo ""
echo "=========================================="
echo "Cleanup complete"
echo "=========================================="
