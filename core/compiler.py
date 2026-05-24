import os
import subprocess
import tempfile
import sys
import shutil

class CodeCompiler:
    @staticmethod
    def run_code(code_content, language="python", timeout=5.0):
        """
        Executes code safely in a sandbox directory with a timeout.
        Returns (stdout, stderr, exit_code).
        """
        # Create unique sandbox dir inside local workspace sandbox
        sandbox_base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sandbox")
        os.makedirs(sandbox_base, exist_ok=True)
        
        # Determine file extension and execution command
        ext = ""
        cmd = []
        
        if language.lower() == "python":
            ext = ".py"
            # Use current running python interpreter for absolute safety and consistency
            cmd = [sys.executable]
        elif language.lower() == "javascript":
            ext = ".js"
            # Attempt to find node
            node_path = shutil.which("node")
            if node_path:
                cmd = [node_path]
            else:
                return ("", "Error: Node.js runtime not found on this system.", -1)
        else:
            return ("", f"Error: Language '{language}' is not supported yet.", -1)

        # Write to temporary file inside sandbox
        fd, temp_file_path = tempfile.mkstemp(suffix=ext, dir=sandbox_base)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            # Execute in subprocess with isolated environment
            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), # Critical for Windows
                "COMSPEC": os.environ.get("COMSPEC", "")
            }
            
            process = subprocess.Popen(
                cmd + [temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=clean_env,
                cwd=sandbox_base
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return (stdout, stderr, process.returncode)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return (stdout, stderr + f"\n[Execution Timed Out after {timeout} seconds]", -1)
                
        except Exception as e:
            return ("", f"Exception occurred during execution: {str(e)}", -1)
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
