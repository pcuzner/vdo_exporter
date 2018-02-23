# vdo_exporter
Python2 based prometheus exporter for VDO volumes. This isn't intended to be a production level solution, but rather a POC to help identify which metrics make the most sense to consumers of the vdo statistics.  

## Background  
Ideally you'd use the python prometheus-client package through rpm, or even pip - but to cut down on these
dependencies I've just used 'standard' python.  

I've tested against vm's with the following configurations;  
   
- RHEL 7.5. beta (kernel 3.10.0-823.el7.x86_64)  
- Ceph 12.2.2 (luminous)  
- python 2.7  
- vdo 6.1.0.98  
- Prometheus 2.0 (container - docker.io/prom/prometheus)
- Grafana 4.6.3 (container - docker.io/grafana/grafana)
- SELINUX disabled
- Firewall disabled

## Installation  
1. donwload and extract the archive  
2. cd to the vdo_exporter directory  
3. install vdo_exporter  
```bash
> python setup.py install --record installed_files
```
Optionally copy the systemd file 
```bash
> cp systemd/vdo_exporter.service /etc/systemd/system
> systemctl daemon-reload
> systemctl enable vdo_exporter
> systemctl start vdo_exporter
```

## Running  
By default the vdo_exporter daemon will bind to 0.0.0.0, listening on port 9285. You'll see
the success of scrape requests in the daemon's output.  



## Prometheus Configuration  
Update prometheus.yml to include a scrape job for the hosts that have the vdo_exporter running.  
e.g. under scrape_configs
```yaml
  # VDO enabled hosts
  - job_name: "vdo_stats"
    static_configs:
      - targets: [ '10.90.90.82:9285', '10.90.90.123:9285', '10.90.90.121:9285']
```
then reload prometheus (SIGHUP)

## Grafana Configuration  
I've included a dashboard to show some of the stats the exporter provides. Just import the 
the 'VDO Tests.json' dashboard into Grafana, then open the dashboard.  
  
You should see something like  
![screenshot](/screenshots/vdo_dashboard.png)


