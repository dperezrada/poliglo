import os
import re
import fnmatch

def main():
    valid_extensions = {
        'py': {'start': r"#req:", 'end': r'#end req', 'comment_symbol': r'^#'}
    }
    found_dependencies = {}

    for valid_extension, req_match in valid_extensions.iteritems():
        found_dependencies[valid_extension] = set()
        for worker_path in os.environ.get('WORKERS_PATHS').split(":"):
            for root, _, filenames in os.walk(worker_path):
                for filename in fnmatch.filter(filenames, '*.'+valid_extension):
                    in_req = False
                    with open(os.path.join(root, filename)) as _file:
                        for line in _file:
                            line = line.strip()
                            if line == req_match.get('start'):
                                in_req = True
                                continue
                            if line == req_match.get('end'):
                                in_req = False
                                continue
                            if in_req:
                                found_dependencies[valid_extension].add(re.sub(
                                    req_match.get('comment_symbol'), '', line
                                ).strip())
    for extension, workers in found_dependencies.iteritems():
        for worker in workers:
            print "%s\t%s" % (extension, worker)

if __name__ == '__main__':
    main()
