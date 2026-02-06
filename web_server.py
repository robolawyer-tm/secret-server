#!/usr/bin/env python3
from flask import Flask, request, jsonify, session, send_from_directory
import json
import os
from lib import auth, storage, crypto, utils

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)  # Generate random secret key for sessions

# CORS headers for development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.before_request
def restrict_access():
    """
    Security Gatekeeper:
    Only allow access from:
    1. Localhost (The phone itself)
    2. Devices on the Hotspot Subnet
    """
    remote_ip = request.remote_addr
    
    # 1. Allow Localhost
    if remote_ip == '127.0.0.1' or remote_ip == 'localhost':
        return None  # Access Granted
        
    # 2. Allow Hotspot Subnet Clients
    from lib import network
    
    # Check 1: Is it in the subnet? (Fast, robust)
    if network.is_ip_in_hotspot_subnet(remote_ip):
         return None # Access Granted
         
    # Check 2: (Backup) Is it in ARP table? (Legacy check)
    allowed_peers = network.get_connected_peers()
    if remote_ip in allowed_peers:
        return None  # Access Granted
        
    # 3. Deny Everyone Else
    print(f"SECURITY ALERT: Blocked access attempt from {remote_ip}")
    return jsonify({
        'error': f'Access Denied: You must be connected to the secure hotspot. Your IP was detected as: {remote_ip}'
    }), 403

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if auth.check_auth(username, password):
        session['username'] = username
        # Create server-side session id and store encrypted credentials
        session_id = os.urandom(24).hex()
        session['session_id'] = session_id
        from lib import session_store
        session_store.save_session_credentials(session_id, username, password)
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Check if user already exists
    auth_file = os.path.join("db", username, "auth.json")
    if os.path.exists(auth_file):
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    if auth.save_auth(username, password):
        session['username'] = username
        # Create server-side session id and store encrypted credentials
        session_id = os.urandom(24).hex()
        session['session_id'] = session_id
        from lib import session_store
        session_store.save_session_credentials(session_id, username, password)
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session"""
    session_id = session.get('session_id')
    if session_id:
        from lib import session_store
        session_store.clear_session(session_id)
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check', methods=['GET'])
def check_auth_status():
    """Check if user is authenticated"""
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username']
        })
    return jsonify({'authenticated': False})

@app.route('/api/apps', methods=['GET'])
def list_apps():
    """List all apps for the authenticated user"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    user_dir = os.path.join('db', username)
    
    if not os.path.exists(user_dir):
        return jsonify({'apps': []})
    
    apps = []
    for item in os.listdir(user_dir):
        item_path = os.path.join(user_dir, item)
        if os.path.isdir(item_path) and item != 'auth.json':
            # Check if secret.json exists
            secret_file = os.path.join(item_path, 'secret.json')
            if os.path.exists(secret_file):
                # Get metadata
                stat = os.stat(secret_file)
                apps.append({
                    'name': item,
                    'modified': stat.st_mtime,
                    'size': stat.st_size
                })
    
    return jsonify({'apps': apps})

@app.route('/api/secrets/store', methods=['POST'])
def store_secret():
    """Store a new encrypted secret"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    app_name = data.get('app_name')
    app_username = data.get('app_username', '')
    secret_text = data.get('secret_text')
    passphrase = data.get('passphrase')
    
    if not all([app_name, secret_text, passphrase]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = session['username']
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    from lib import session_store
    user_password = session_store.get_session_password(session_id)
    if not user_password:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    
    try:
        # Encrypt the secret
        encrypted_data = crypto.encrypt_secret(secret_text, passphrase)
        if not encrypted_data.ok:
            return jsonify({'error': f'Encryption failed: {encrypted_data.status}'}), 500
        
        # Create payload
        payload = {
            'app_username': app_username,
            'password': str(encrypted_data),
            'timestamp': __import__('datetime').datetime.now().strftime("%Y%m%d-%H%M%S")
        }
        
        # Store it
        filename = storage.store_payload(username, app_name, user_password, payload)
        return jsonify({'success': True, 'filename': filename})
        
    except PermissionError:
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets/retrieve', methods=['POST'])
def retrieve_secret():
    """Retrieve and decrypt a secret"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    app_name = data.get('app_name')
    passphrase = data.get('passphrase')
    
    if not all([app_name, passphrase]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = session['username']
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    from lib import session_store
    user_password = session_store.get_session_password(session_id)
    if not user_password:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    
    try:
        result = storage.retrieve_latest_payload(username, app_name, user_password)
        if not result:
            return jsonify({'error': 'No secret found'}), 404
        
        data_str, filepath = result
        payload = json.loads(data_str)
        encrypted_text = payload['password']
        app_username = payload.get('app_username', 'N/A')
        timestamp = payload.get('timestamp', 'Unknown')
        
        # Decrypt
        decrypted_data = crypto.decrypt_secret(encrypted_text, passphrase)
        if decrypted_data.ok:
            return jsonify({
                'success': True,
                'secret': decrypted_data.data.decode('utf-8'),
                'app_username': app_username,
                'timestamp': timestamp
            })
        else:
            return jsonify({'error': f'Decryption failed: {decrypted_data.status}'}), 400
            
    except PermissionError:
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets/update', methods=['POST'])
def update_secret():
    """Update a secret by overwriting with a new value (or JSON object)"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    app_name = data.get('app_name')
    passphrase = data.get('passphrase')
    key_path = data.get('key_path')
    value = data.get('value')
    
    if not all([app_name, passphrase, value is not None]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = session['username']
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    from lib import session_store
    user_password = session_store.get_session_password(session_id)
    if not user_password:
        return jsonify({'error': 'Missing session credentials; please login again'}), 401
    
    try:
        # 1. Retrieve existing secret
        result = storage.retrieve_latest_payload(username, app_name, user_password)
        if not result:
            return jsonify({'error': 'No secret found to update'}), 404
        
        data_str, filepath = result
        payload = json.loads(data_str)
        encrypted_text = payload['password']
        app_username = payload.get('app_username', '')
        
        # Decrypt
        decrypted_data = crypto.decrypt_secret(encrypted_text, passphrase)
        if not decrypted_data.ok:
            return jsonify({'error': f'Decryption failed: {decrypted_data.status}'}), 400
        
        current_json_str = decrypted_data.data.decode('utf-8')
        
        # Parse JSON
        try:
            secret_data = json.loads(current_json_str)
        except json.JSONDecodeError:
            # Not JSON, wrap it
            secret_data = {'raw_content': current_json_str}
        
        # 2. Apply update (Full overwrite if no key_path)
        if not key_path:
            # Full overwrite
            try:
                secret_data = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                secret_data = value
        else:
            # Apply deep update (backwards compatibility for non-polished clients)
            utils.deep_update(secret_data, key_path, value)
        
        # 3. Re-encrypt and store
        new_json_str = json.dumps(secret_data, indent=2) if isinstance(secret_data, (dict, list)) else str(secret_data)
        
        encrypted_data = crypto.encrypt_secret(new_json_str, passphrase)
        
        if not encrypted_data.ok:
            return jsonify({'error': f'Encryption failed: {encrypted_data.status}'}), 500
        
        new_payload = {
            'app_username': app_username,
            'password': str(encrypted_data),
            'timestamp': __import__('datetime').datetime.now().strftime("%Y%m%d-%H%M%S")
        }
        
        filename = storage.store_payload(username, app_name, user_password, new_payload)
        
        return jsonify({
            'success': True,
            'updated_secret': secret_data,
            'filename': filename
        })
        
    except TypeError as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 400
    except PermissionError:
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/secrets/metadata/<app_name>', methods=['GET'])
def get_secret_metadata(app_name):
    """Get metadata for a specific app's secret"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    secret_file = os.path.join('db', username, app_name, 'secret.json')
    
    if not os.path.exists(secret_file):
        return jsonify({'error': 'Secret not found'}), 404
    
    try:
        with open(secret_file, 'r') as f:
            payload = json.load(f)
        
        stat = os.stat(secret_file)
        return jsonify({
            'app_username': payload.get('app_username', 'N/A'),
            'timestamp': payload.get('timestamp', 'Unknown'),
            'modified': stat.st_mtime,
            'size': stat.st_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure db directory exists
    os.makedirs('db', exist_ok=True)
    print("Starting web server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
