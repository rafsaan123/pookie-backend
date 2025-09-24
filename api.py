#!/usr/bin/env python3
"""
Multi-Project BTEB Results API Server using Supabase Database
Production-ready version for Vercel deployment with full functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from typing import Dict, List, Optional, Any

app = Flask(__name__)
CORS(app)

# Production configuration
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Initialize Supabase manager with error handling
try:
    from multi_supabase import get_supabase_client, supabase_manager
    from web_api_fallback import search_student_in_web_apis, test_web_api_connections, list_web_apis
    SUPABASE_AVAILABLE = True
    print("✅ Supabase modules loaded successfully")
except Exception as e:
    print(f"❌ Error loading Supabase modules: {e}")
    SUPABASE_AVAILABLE = False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({
                'status': 'unhealthy',
                'supabase_connected': False,
                'error': 'Supabase modules not available'
            }), 500
        
        # Test current project connection
        supabase = get_supabase_client()
        result = supabase.table('programs').select('*').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'supabase_connected': True,
            'database': 'supabase',
            'current_project': supabase_manager.current_project,
            'available_projects': list(supabase_manager.projects.keys()),
            'message': 'API server is running and connected to Supabase (Production Ready)'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'supabase_connected': False,
            'error': str(e)
        }), 500

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all available Supabase projects"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        projects_info = {}
        for name, project in supabase_manager.projects.items():
            projects_info[name] = {
                'name': name,
                'description': project.description,
                'url': project.url,
                'is_active': name == supabase_manager.current_project
            }
        return jsonify(projects_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_name>/test', methods=['GET'])
def test_project(project_name):
    """Test connection to a specific project"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        # Switch to the project temporarily
        original_project = supabase_manager.current_project
        supabase_manager.switch_project(project_name)
        
        try:
            supabase = get_supabase_client()
            result = supabase.table('programs').select('*').limit(1).execute()
            
            return jsonify({
                'project': project_name,
                'status': 'connected',
                'message': 'Project connection successful'
            })
        finally:
            # Restore original project
            supabase_manager.switch_project(original_project)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_name>/switch', methods=['POST'])
def switch_project(project_name):
    """Switch to a different Supabase project"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        if project_name not in supabase_manager.projects:
            return jsonify({'error': f'Project {project_name} not found'}), 404
        
        supabase_manager.switch_project(project_name)
        
        return jsonify({
            'message': f'Switched to project: {project_name}',
            'current_project': project_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web-apis', methods=['GET'])
def list_web_apis():
    """List all configured web APIs"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        apis = list_web_apis()
        return jsonify(apis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web-apis/test', methods=['GET'])
def test_web_apis():
    """Test all web API connections"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        results = test_web_api_connections()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-result', methods=['POST'])
def search_result():
    """Search for student results across all Supabase projects with web API fallback"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        roll_no = data.get('rollNo')
        regulation = data.get('regulation')
        program = data.get('program')
        
        if not all([roll_no, regulation, program]):
            return jsonify({'error': 'Missing required fields: rollNo, regulation, program'}), 400
        
        print(f"🔍 Searching for: {roll_no}, {regulation}, {program}")
        
        # Search across Supabase projects
        result = supabase_manager.search_student_across_projects(roll_no, regulation, program)
        
        print(f"🔍 Search result: {result}")
        
        if result and result.get('student_data'): # Check for 'student_data' to confirm a student was found
            # Get CGPA data if available
            cgpa_data = []
            if result.get('source') == 'supabase':
                # Search for CGPA records across all projects
                for project_name in supabase_manager.get_search_order():
                    try:
                        supabase_manager.switch_project(project_name)
                        supabase = get_supabase_client()
                        
                        cgpa_records = supabase.table('cgpa_records').select('*').eq('roll_number', roll_no).execute()
                        
                        if cgpa_records.data:
                            for cgpa_record in cgpa_records.data:
                                cgpa_data.append({
                                    'semester': cgpa_record.get('semester', 'Final'),
                                    'cgpa': str(cgpa_record.get('cgpa', '0.00')),
                                    'publishedAt': cgpa_record.get('created_at', '2025-01-01T00:00:00Z')
                                })
                            break  # Stop searching once we find CGPA data
                    except Exception as e:
                        print(f"❌ Error getting CGPA from {project_name}: {e}")
                        continue
                
                # Restore original project
                supabase_manager.switch_project(result.get('project_name', 'primary'))
            
            # Add CGPA data to result
            if cgpa_data:
                result['cgpaData'] = cgpa_data
            
            # Get GPA records - check if they come from web API fallback or need to fetch from Supabase
            gpa_records = []
            if result.get('source', '').startswith('web_api'):
                # GPA records come from web API fallback
                gpa_records = result.get('gpa_records', [])
                print(f"📊 Using {len(gpa_records)} GPA records from web API fallback")
            else:
                # Fetch GPA records from Supabase (separate query) - use the same project where student was found
                try:
                    # Switch to the project where the student was found
                    found_project = result.get('project_name', 'primary')
                    supabase_manager.switch_project(found_project)
                    supabase = get_supabase_client()
                    
                    gpa_result = supabase.table('gpa_records').select('*').eq('roll_number', roll_no).order('semester').execute()
                    gpa_records = gpa_result.data if gpa_result.data else []
                    print(f"📊 Found {len(gpa_records)} GPA records in {found_project}")
                except Exception as e:
                    print(f"❌ Error fetching GPA records: {e}")
                    gpa_records = []
            
            # Transform the data to match mobile app expectations
            transformed_data = {
                'success': True,
                'roll': result['student_data']['roll_number'],
                'regulation': result['student_data']['regulation_year'],
                'exam': result['student_data']['program_name'],
                'instituteData': {
                    'code': result['institute_data']['institute_code'],
                    'name': result['institute_data']['name'],
                    'district': result['institute_data']['district']
                },
                'resultData': [],  # Will be populated from GPA records
                'cgpaData': result.get('cgpaData', [])
            }
            
            # Add semester results from GPA records
            if gpa_records:
                for gpa_record in gpa_records:
                    # Handle ref_subjects - convert to array if it's a string or None
                    ref_subjects = gpa_record.get('ref_subjects', [])
                    if isinstance(ref_subjects, str):
                        # If it's a string, try to parse it as JSON or split by comma
                        try:
                            import json
                            ref_subjects = json.loads(ref_subjects)
                        except:
                            ref_subjects = [ref_subjects] if ref_subjects else []
                    elif ref_subjects is None:
                        ref_subjects = []
                    
                    semester_result = {
                        'publishedAt': gpa_record.get('created_at', '2025-01-01T00:00:00Z'),
                        'semester': str(gpa_record.get('semester', 1)),
                        'result': {
                            'gpa': str(gpa_record.get('gpa', '0.00')) if gpa_record.get('gpa') is not None else 'ref',
                            'ref_subjects': ref_subjects
                        },
                        'passed': not gpa_record.get('is_reference', False),
                        'gpa': str(gpa_record.get('gpa', '0.00')) if gpa_record.get('gpa') is not None else 'ref'
                    }
                    transformed_data['resultData'].append(semester_result)
            
            return jsonify(transformed_data)
        else:
            # Try web API fallback
            print(f"🌐 Student not found in any Supabase project, trying web APIs...")
            web_result = search_student_in_web_apis(roll_no, regulation, program)
            
            if web_result and web_result.get('success'):
                return jsonify(web_result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Student not found in any database or web API',
                    'roll': roll_no,
                    'regulation': regulation,
                    'exam': program,
                    'projects_searched': supabase_manager.get_search_order(),
                    'web_apis_tried': ['btebresulthub']
                }), 404
                
    except Exception as e:
        print(f"❌ Error in search_result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regulations/<program>', methods=['GET'])
def get_regulations(program):
    """Get available regulations for a program"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        supabase = get_supabase_client()
        result = supabase.table('regulations').select('regulation_year').eq('program_name', program).execute()
        
        regulations = [row['regulation_year'] for row in result.data]
        return jsonify({'regulations': regulations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check environment variables and project status"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not available'}), 500
            
        debug_info = {
            'environment_variables': {
                'SUPABASE_PRIMARY_URL': os.getenv('SUPABASE_PRIMARY_URL', 'NOT_SET'),
                'SUPABASE_PRIMARY_KEY': os.getenv('SUPABASE_PRIMARY_KEY', 'NOT_SET')[:20] + '...' if os.getenv('SUPABASE_PRIMARY_KEY') else 'NOT_SET',
                'SUPABASE_SECONDARY_URL': os.getenv('SUPABASE_SECONDARY_URL', 'NOT_SET'),
                'SUPABASE_SECONDARY_KEY': os.getenv('SUPABASE_SECONDARY_KEY', 'NOT_SET')[:20] + '...' if os.getenv('SUPABASE_SECONDARY_KEY') else 'NOT_SET',
            },
            'loaded_projects': list(supabase_manager.projects.keys()),
            'current_project': supabase_manager.current_project,
            'search_order': supabase_manager.search_order
        }
        
        # Test if we can actually connect to Supabase
        try:
            supabase = get_supabase_client()
            test_result = supabase.table('programs').select('*').limit(1).execute()
            debug_info['supabase_connection'] = 'SUCCESS'
            debug_info['test_query_result'] = len(test_result.data) if test_result.data else 0
        except Exception as e:
            debug_info['supabase_connection'] = f'FAILED: {str(e)}'
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # For production deployment (Render, Heroku, etc.)
    pass