## crontab entry for the RSS-inator

0 8 * * * source venvs/core/bin/activate; export PYTHONPATH=$PYTHONPATH:$HOME/Desktop/projects/operation-clusterfuck/daily_reports; papermill /home/emily/Desktop/projects/operation-clusterfuck/daily_reports/RSS-inator.ipynb /tmp/RSS-inator.ipynb
