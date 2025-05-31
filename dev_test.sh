#!/usr/bin/env bash
# ----------------------------------------------------------------
# dev_test.sh
#
# Quick development script for testing individual pipeline steps
# Usage: 
#   ./dev_test.sh 7           # Test step 7 only
#   ./dev_test.sh 1-3         # Test steps 1 through 3
#   ./dev_test.sh all         # Test all steps
# ----------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${BLUE}🔧 Football Bot Development Tester${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo "Usage:"
    echo -e "  ${YELLOW}./dev_test.sh 7${NC}           # Test step 7 only"
    echo -e "  ${YELLOW}./dev_test.sh 1-3${NC}         # Test steps 1 through 3"
    echo -e "  ${YELLOW}./dev_test.sh all${NC}         # Test all steps"
    echo ""
    echo "Available steps: 1, 2, 3, 4, 5, 6, 7"
    exit 1
fi

case $1 in
    "1")
        echo -e "${GREEN}🧪 Testing Step 1...${NC}"
        python3 step1.py
        ;;
    "2")
        echo -e "${GREEN}🧪 Testing Step 2...${NC}"
        cd step2 && python3 step2.py && cd ..
        ;;
    "3")
        echo -e "${GREEN}🧪 Testing Step 3...${NC}"
        cd step3 && python3 step3.py && cd ..
        ;;
    "4")
        echo -e "${GREEN}🧪 Testing Step 4...${NC}"
        cd step4 && python3 step4.py && cd ..
        ;;
    "5")
        echo -e "${GREEN}🧪 Testing Step 5...${NC}"
        cd step5 && python3 step5.py && cd ..
        ;;
    "6")
        echo -e "${GREEN}🧪 Testing Step 6...${NC}"
        cd step6 && python3 step6.py && cd ..
        ;;
    "7")
        echo -e "${GREEN}🧪 Testing Step 7...${NC}"
        python3 step7.py
        ;;
    "all")
        echo -e "${GREEN}🧪 Testing All Steps...${NC}"
        echo -e "${BLUE}Step 1:${NC}"
        python3 step1.py
        echo -e "\n${BLUE}Step 2:${NC}"
        cd step2 && python3 step2.py && cd ..
        echo -e "\n${BLUE}Step 3:${NC}"
        cd step3 && python3 step3.py && cd ..
        echo -e "\n${BLUE}Step 4:${NC}"
        cd step4 && python3 step4.py && cd ..
        echo -e "\n${BLUE}Step 5:${NC}"
        cd step5 && python3 step5.py && cd ..
        echo -e "\n${BLUE}Step 6:${NC}"
        cd step6 && python3 step6.py && cd ..
        echo -e "\n${BLUE}Step 7:${NC}"
        python3 step7.py
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo "Use: 1, 2, 3, 4, 5, 6, 7, or all"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Test completed!${NC}"
