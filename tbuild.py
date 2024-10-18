# import os
# import shutil

# def remove_docs_and_tests(directory):
#     for root, dirs, files in os.walk(directory):
#         for dir in dirs:
#             if dir in ['doc', 'docs', 'test', 'tests']:
#                 shutil.rmtree(os.path.join(root, dir))

# def remove_pyc_files(directory):
#        for root, dirs, files in os.walk(directory):
#            for file in files:
#                if file.endswith('.pyc'):
#                    os.remove(os.path.join(root, file))
# dir_path = r'E:\tool\PyStand-py310-x64\site-packages'
# remove_docs_and_tests(dir_path)
# remove_pyc_files(dir_path)


from modulegraph import modulegraph
graph = modulegraph.ModuleGraph()
graph.run_script("run.py")