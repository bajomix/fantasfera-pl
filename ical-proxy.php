<?php
$url = 'https://calendar.google.com/calendar/ical/2da0751953a6122c8f81e7f4840092cac413ef4c5a4070ff395bcf0c3c450b2e%40group.calendar.google.com/public/basic.ics';

if (function_exists('curl_init')) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS      => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_USERAGENT      => 'Mozilla/5.0 (compatible; CalendarFetcher/1.0)',
        CURLOPT_HTTPHEADER     => ['Accept: text/calendar'],
    ]);
    $data = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($data === false || $httpCode !== 200) $data = false;
} else {
    $ctx = stream_context_create(['http' => [
        'timeout'    => 15,
        'user_agent' => 'Mozilla/5.0 (compatible; CalendarFetcher/1.0)',
        'header'     => 'Accept: text/calendar',
    ]]);
    $data = @file_get_contents($url, false, $ctx);
}

if ($data === false || strpos($data, 'BEGIN:VCALENDAR') === false) {
    http_response_code(502);
    header('Content-Type: text/plain');
    exit('error');
}

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: max-age=300');
echo $data;
