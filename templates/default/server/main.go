package main

import (
	"log"
	"net"

	"golang.org/x/net/context"
	"google.golang.org/grpc"
	pb {{ pb_import_path }}
)

const (
	port = ":50051"
)

type server struct{}



func main() {
	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	s := grpc.NewServer()
	pb.{{ register_server_call }}
	s.Serve(lis)
}
