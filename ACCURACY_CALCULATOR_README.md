# Jarvis Accuracy Calculator

This directory contains tools for calculating and monitoring the accuracy of your Jarvis AI assistant.

## Files Created

### 1. `calculate_accuracy.py` (Basic Version)
- **Purpose**: Quick accuracy calculation with simulated tests
- **Best for**: Initial testing, demonstration purposes
- **Tests**: Speech recognition, response times, command execution
- **Output**: Terminal display + JSON report

### 2. `advanced_accuracy_calculator.py` (Advanced Version) ⭐ RECOMMENDED
- **Purpose**: Comprehensive testing of actual system components
- **Best for**: Production monitoring, real performance analysis
- **Tests**: 
  - ✅ Microphone system functionality
  - ✅ Assistant status updates
  - ✅ Response time measurements
  - ✅ Module import verification
  - ✅ File operation performance
- **Output**: Detailed terminal display + JSON + Text summary

## How to Use

### Quick Start (Recommended)

```bash
# Run the advanced calculator
python advanced_accuracy_calculator.py
```

### Basic Version

```bash
# Run the basic calculator
python calculate_accuracy.py
```

## What Gets Measured

### Accuracy Categories

1. **Microphone System** (20% weight)
   - Status toggle functionality
   - Read/write operations
   - Status restoration

2. **Assistant Status** (20% weight)
   - Status update accuracy
   - Status retrieval reliability
   - Multiple status testing

3. **Response Times** (15% weight)
   - File I/O speed
   - Status retrieval speed
   - Overall system responsiveness

4. **Module Imports** (25% weight)
   - RealtimeSearchEngine
   - ChatBot
   - TextToSpeech
   - Model/Decision Making

5. **File Operations** (20% weight)
   - Write speed
   - Read speed
   - Data integrity

### Scoring System

- **A+ (90-100%)**: 🏆 Excellent - Production ready
- **A (80-89%)**: ✅ Good - Minor improvements possible
- **B (70-79%)**: ⚠️ Fair - Some issues need attention
- **C (60-69%)**: ❌ Needs Improvement - Several issues
- **D (<60%)**: 🚨 Critical - Immediate attention required

## Output Files

Results are saved in the `Data/` directory:

1. **JSON Report**: `detailed_accuracy_YYYYMMDD_HHMMSS.json`
   - Complete test results
   - All metrics and details
   - Machine-readable format

2. **Text Summary**: `accuracy_summary_YYYYMMDD_HHMMSS.txt`
   - Quick overview
   - Human-readable format
   - Easy to share

## Example Output

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🤖 ADVANCED JARVIS ACCURACY ANALYZER 🤖            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

🎯 OVERALL PERFORMANCE
┌─────────────────────────────┐
│ Overall System Accuracy     │
│                             │
│ 85.50%  ✅                  │
│                             │
│ Grade: A GOOD               │
└─────────────────────────────┘

📋 DETAILED CATEGORY RESULTS:

┌──────────────────────┬───────────┬───────────┬────────────┐
│ Category             │ Accuracy  │ Details   │ Status     │
├──────────────────────┼───────────┼───────────┼────────────┤
│ Microphone System    │ 100.0%    │ 3/3       │ ✅ PASS    │
│ Assistant Status     │ 100.0%    │ 5/5       │ ✅ PASS    │
│ Response Times       │ 70.0%     │ -         │ ⚡ FAST    │
│ Module Imports       │ 100.0%    │ 4/4       │ ✅ PASS    │
│ File Operations      │ 100.0%    │ 2/2       │ ✅ PASS    │
└──────────────────────┴───────────┴───────────┴────────────┘

💡 RECOMMENDATIONS:
  🟢 System is performing well!
     - Continue monitoring
     - Run tests regularly

✨ Analysis completed successfully!
```

## Integration with Main System

The accuracy calculator integrates with your existing Jarvis system:

- Uses actual GUI functions (`GetMicrophoneStatus`, `SetAssistantStatus`)
- Tests real file operations in `Frontend/Files/`
- Verifies module imports from `Backend/`
- Measures actual response times

## Automated Testing

You can run accuracy tests automatically:

```bash
# Run every hour (Linux/Mac cron job)
0 * * * * cd /path/to/jvis\ 2.0 && python advanced_accuracy_calculator.py >> accuracy.log

# Run on startup (Windows Task Scheduler)
schtasks /create /tn "JarvisAccuracy" /tr "python advanced_accuracy_calculator.py" /sc onlogon
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r Requirements.txt
   ```

2. **Permission errors**
   - Run as administrator/root
   - Check folder permissions

3. **Low accuracy scores**
   - Check microphone hardware
   - Verify all dependencies installed
   - Review error logs in terminal

### Interpreting Results

- **High accuracy (>80%)**: System is healthy
- **Medium accuracy (60-80%)**: Some components need attention
- **Low accuracy (<60%)**: Critical issues, check logs

## Best Practices

1. **Run Regularly**: Test accuracy daily or weekly
2. **Save Reports**: Keep historical data for trend analysis
3. **Monitor Trends**: Watch for gradual degradation
4. **Test After Changes**: Always run after updates/modifications
5. **Set Baseline**: Establish normal accuracy levels for your system

## Customization

You can modify test parameters in `advanced_accuracy_calculator.py`:

```python
TEST_CONFIG = {
    "speech_recognition_tests": 10,  # Number of tests
    "response_time_tests": 5,
    "accuracy_threshold": 0.75,  # Pass threshold
}
```

## Support

For issues or questions:
1. Check terminal output for specific error messages
2. Review saved JSON reports for detailed diagnostics
3. Verify all dependencies are installed
4. Check microphone and system permissions

---

**Created**: 2026-03-04  
**Version**: 1.0  
**Author**: Jarvis Development Team
