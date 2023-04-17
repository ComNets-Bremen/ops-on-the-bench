LOGIN_URL=http://192.168.142.128:8000/omnetppManager/login/
YOUR_USER='srikanth'
YOUR_PASS='MSKmsk@635'
COOKIES=cookies.txt
CURL_BIN="curl -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"

echo -n "Django Auth: get csrftoken ..."
$CURL_BIN $LOGIN_URL > /dev/null
DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken\s*//')"

echo "csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken\s*//')"
echo -n " perform login ..."
$CURL_BIN \
    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
    -X POST http://192.168.142.128:8000/omnetppManager/login/
#$LOGIN_URL

echo -n " do something while logged in ..."

#$CURL_BIN \
#    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
#    -X POST http://192.168.142.128:8000/omnetppManager/export-simulation-stats/ > sim.json
    
#$CURL_BIN \
#    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
#    -X POST http://192.168.142.128:8000/omnetppManager/queue_status/ > Qstatus.html

$CURL_BIN \
    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
    -X POST http://192.168.142.128:8000/omnetppManager/get-server-config/ > serverconfig.json

##echo " logout"
##rm $COOKIES
#echo "$PWD"

#SCRIPT="${PWD}/trainer.py"

#echo "$SCRIPT"

#python3 $SCRIPT status.html simulation-meta_26_02_2023.json

##python3 $SCRIPT Qstatus.html sim.json
