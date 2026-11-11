pid=$(systemctl --user show -p MainPID --value privyhub-companion)
export $(tr '\0' '\n' < /proc/$pid/environ | grep '^DISPLAY=\|^XAUTHORITY=' | xargs)
