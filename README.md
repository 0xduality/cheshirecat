# Setup

## Home directory
Move the script to your home directory. When the cron job
runs it starts there and the script will read wallet data 
from/write wallet data to a file in the same directory.

## Requirements
- pip3 install requests
- pip3 install beautifulsoup4
- pip3 install web3

## Wallet Information
The first time it runs it will ask you for your address 
and private key and save them to a file. Afterwards it 
will read them from that file.

## Cron 
Set the timezone of your computer to UTC. 
Then enter
```
crontab -e
```
and in the editor append these lines
```
58 5   *   *   *     python3 autoredeem.py 
58 13  *   *   *     python3 autoredeem.py 
58 21  *   *   *     python3 autoredeem.py
```
