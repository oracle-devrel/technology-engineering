wait_file() {
    echo "Waiting File $1"
    x=60
    until [ -f $1 ]
    do
        x=$(( $x - 1 ))
        if [ $x -eq 0 ]; then
          echo "ERROR: $1 not found"
          exit 1
        fi
        echo "- waiting 5 secs"
        sleep 5
    done
    echo "File found"
}