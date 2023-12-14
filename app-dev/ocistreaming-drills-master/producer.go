package main

import (
	"context"
	"fmt"
	"strconv"

	"github.com/oracle/oci-go-sdk/v49/common"
	"github.com/oracle/oci-go-sdk/v49/example/helpers"
	"github.com/oracle/oci-go-sdk/v49/streaming"
)

const ociMessageEndpoint = "https://cell-1.streaming.eu-frankfurt-1.oci.oraclecloud.com"
const ociStreamOcid = "ocid1.stream.oc1.eu-frankfurt-1.amaaaaaauevftmqaikcwu43ouqq6lz2jhfrwevh3yrh2u6q4zpzcss5zvvuq"
const ociConfigFilePath = "/home/fernando_h/.oci/config"
const ociProfileName = "DEFAULT"

func main() {
	fmt.Println("Go oci oss sdk example producer")
	putMsgInStream(ociMessageEndpoint, ociStreamOcid)
}

func putMsgInStream(streamEndpoint string, streamOcid string) {
	fmt.Println("Stream endpoint for put msg api is: " + streamEndpoint)

	provider, err := common.ConfigurationProviderFromFileWithProfile(ociConfigFilePath, ociProfileName, "")
	helpers.FatalIfError(err)

	streamClient, err := streaming.NewStreamClientWithConfigurationProvider(provider, streamEndpoint)
	helpers.FatalIfError(err)

	// Create a request and dependent object(s).
	for i := 0; i < 5; i++ {
		putMsgReq := streaming.PutMessagesRequest{StreamId: common.String(streamOcid),
			PutMessagesDetails: streaming.PutMessagesDetails{
				// we are batching 2 messages for each Put Request
				Messages: []streaming.PutMessagesDetailsEntry{
					{Key: []byte("key dummy-0-" + strconv.Itoa(i)),
						Value: []byte("value dummy-" + strconv.Itoa(i))},
					{Key: []byte("key dummy-1-" + strconv.Itoa(i)),
						Value: []byte("value dummy-" + strconv.Itoa(i))}}},
		}

		// Send the request using the service client
		putMsgResp, err := streamClient.PutMessages(context.Background(), putMsgReq)
		helpers.FatalIfError(err)

		// Retrieve value from the response.
		fmt.Println(putMsgResp)
	}

}