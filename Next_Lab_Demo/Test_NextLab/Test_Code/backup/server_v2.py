from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import os
import logging

# Set up logging
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        logging.info(f'GET request for {self.path} line 11')
        if self.path == '/Drohnen_GmbH':
            logging.info(f' {self.path} connected line 13')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"message": "Hello, world!"}')
            logging.info(f' {self.path} finished line 18')
        else:
            super().do_GET()

    def do_POST(self):
        logging.info(f'POST request for {self.path} line21')
        if self.path == '/Drohnen_GmbH':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                json_data = json.loads(post_data)
                print("Received JSON data:", json_data)

                # Load existing data from main JSON file
                main_json_file = 'main.json'
                if os.path.exists(main_json_file):
                    with open(main_json_file, 'r') as file:
                        try:
                            main_data = json.load(file)
                        except json.JSONDecodeError:
                            main_data = []
                else:
                    main_data = []

                # Append the new data
                main_data.append(json_data)

                # Write the updated data back to the main JSON file
                with open(main_json_file, 'w') as file:
                    json.dump(main_data, file, indent=4)

                self.send_response(200)
                logging.info(f'response send {200} line50')
                self.send_header('Content-type', 'application/json')
                logging.info(f'header send {200} line 52')
                self.end_headers()
                logging.info(f'header end {200} line 54')
                response = {'message': 'JSON received and stored successfully'}
                logging.info(f'response text {response} line 56')
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'Invalid JSON'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        logging.info(f'DELETE request for {self.path} line 63')
        if self.path == '/Drohnen_GmbH':
            content_length = int(self.headers['Content-Length'])
            delete_data = self.rfile.read(content_length)
            try:
                json_data = json.loads(delete_data)
                print("Received JSON data for deletion:", json_data)

                key = json_data.get('key')
                condition_value = json_data.get('value')

                if not key or condition_value is None:
                    raise ValueError("Invalid key or value")

                # Load existing data from main JSON file
                main_json_file = 'main.json'
                if os.path.exists(main_json_file):
                    with open(main_json_file, 'r') as file:
                        try:
                            main_data = json.load(file)
                        except json.JSONDecodeError:
                            main_data = []
                else:
                    main_data = []

                # Delete the first matching entry
                entry_deleted = False
                updated_data = []

                for entry in main_data:
                    if entry.get(key) == condition_value and not entry_deleted:
                        entry_deleted = True  # Entry found and deleted
                        continue  # Skip this entry
                    updated_data.append(entry)

                # Write the updated data back to the main JSON file
                with open(main_json_file, 'w') as file:
                    json.dump(updated_data, file, indent=4)

                if entry_deleted:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'message': f'Entry with {key} = {condition_value} successfully deleted.'}
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'error': f'No entry with {key} = {condition_value} found.'}
                
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except (json.JSONDecodeError, ValueError) as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': f'Invalid request: {e}'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

PORT = 8310
#Start des Servers lokale IP des PC und Port 
with HTTPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
    print(f"Serving at port {PORT}")
    logging.info(f'Server started at port {PORT} line 129')
    httpd.serve_forever()
