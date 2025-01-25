import http.client, urllib.parse, json

conn = http.client.HTTPConnection('geocode.xyz')

params = urllib.parse.urlencode({
    'locate': 'London',
    'json': 1,
    })

conn.request('GET', '/?{}'.format(params))

res = conn.getresponse()
data = res.read()

co_ord = json.loads(data.decode("utf-8"))

# Print the JSON object
print(co_ord["latt"], co_ord["longt"])