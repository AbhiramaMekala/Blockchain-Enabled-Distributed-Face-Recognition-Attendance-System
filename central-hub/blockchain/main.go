package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"

	abci "github.com/tendermint/tendermint/abci/types"
	"github.com/tendermint/tendermint/config"
	"github.com/tendermint/tendermint/libs/log"
	"github.com/tendermint/tendermint/node"
	"github.com/tendermint/tendermint/p2p"
	"github.com/tendermint/tendermint/privval"
	"github.com/tendermint/tendermint/proxy"
	tmtypes "github.com/tendermint/tendermint/types"
	tmdb "github.com/tendermint/tm-db"

	"github.com/dgraph-io/badger/v2"
)

type AttendanceApp struct {
	abci.BaseApplication
	db       *badger.DB
	lastHash []byte
}

func NewAttendanceApp(path string) *AttendanceApp {
	opts := badger.DefaultOptions(path)
	opts.Logger = nil
	db, err := badger.Open(opts)
	if err != nil {
		panic(err)
	}
	return &AttendanceApp{db: db}
}

func (app *AttendanceApp) CheckTx(req abci.RequestCheckTx) abci.ResponseCheckTx {
	if len(req.Tx) == 0 {
		return abci.ResponseCheckTx{Code: 1, Log: "empty tx"}
	}
	return abci.ResponseCheckTx{Code: 0}
}

func (app *AttendanceApp) DeliverTx(req abci.RequestDeliverTx) abci.ResponseDeliverTx {
	tx := req.Tx
	hash := sha256.Sum256(tx)

	err := app.db.Update(func(t *badger.Txn) error {
		return t.Set(hash[:], tx)
	})
	if err != nil {
		return abci.ResponseDeliverTx{Code: 1, Log: err.Error()}
	}

	app.lastHash = hash[:]

	fmt.Println("Stored TX Hash:", hex.EncodeToString(hash[:]))
	return abci.ResponseDeliverTx{Code: 0}
}

func (app *AttendanceApp) Commit() abci.ResponseCommit {
	return abci.ResponseCommit{Data: app.lastHash}
}

func (app *AttendanceApp) Query(req abci.RequestQuery) abci.ResponseQuery {
	var value []byte

	err := app.db.View(func(txn *badger.Txn) error {
		item, err := txn.Get(req.Data)
		if err != nil {
			return err
		}
		return item.Value(func(val []byte) error {
			value = append([]byte{}, val...)
			return nil
		})
	})

	if err != nil {
		return abci.ResponseQuery{Code: 1, Log: err.Error()}
	}

	return abci.ResponseQuery{Code: 0, Value: value}
}

////////////////////////////////////////////////////////
// 🔥 NEW: HTTP API TO FETCH ALL ATTENDANCE
////////////////////////////////////////////////////////

func (app *AttendanceApp) GetAllAttendance(w http.ResponseWriter, r *http.Request) {

	// Enable CORS
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	var records []map[string]interface{}

	err := app.db.View(func(txn *badger.Txn) error {
		it := txn.NewIterator(badger.DefaultIteratorOptions)
		defer it.Close()

		for it.Rewind(); it.Valid(); it.Next() {
			item := it.Item()

			err := item.Value(func(val []byte) error {
				var rec map[string]interface{}
				if err := json.Unmarshal(val, &rec); err == nil {
					records = append(records, rec)
				}
				return nil
			})
			if err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}

	json.NewEncoder(w).Encode(records)
}

////////////////////////////////////////////////////////

func initChain(root string) {
	cfg := config.DefaultConfig()
	cfg.SetRoot(root)

	config.EnsureRoot(root)

	pv := privval.LoadOrGenFilePV(
		cfg.PrivValidatorKeyFile(),
		cfg.PrivValidatorStateFile(),
	)

	nodeKey, err := p2p.LoadOrGenNodeKey(cfg.NodeKeyFile())
	if err != nil {
		panic(err)
	}

	genFile := cfg.GenesisFile()
	if _, err := os.Stat(genFile); os.IsNotExist(err) {
		genDoc := tmtypes.GenesisDoc{
			ChainID: "attendance-chain",
			Validators: []tmtypes.GenesisValidator{
				{
					Address: pv.Key.PubKey.Address(),
					PubKey:  pv.Key.PubKey,
					Power:   10,
					Name:    "validator-1",
				},
			},
		}
		if err := genDoc.SaveAs(genFile); err != nil {
			panic(err)
		}
	}

	fmt.Println("Initialized Tendermint in", root)
	fmt.Println("Node ID:", nodeKey.ID())
}

func main() {

	home, _ := os.UserHomeDir()
	root := filepath.Join(home, ".attendance-chain")

	if len(os.Args) > 1 && os.Args[1] == "init" {
		initChain(root)
		return
	}

	appDBPath := filepath.Join(root, "data", "attendance")
	os.MkdirAll(appDBPath, 0755)

	cfg := config.DefaultConfig()
	cfg.SetRoot(root)
	cfg.RPC.ListenAddress = "tcp://127.0.0.1:26657"
	cfg.Consensus.CreateEmptyBlocks = false

	pv := privval.LoadOrGenFilePV(
		cfg.PrivValidatorKeyFile(),
		cfg.PrivValidatorStateFile(),
	)

	nodeKey, err := p2p.LoadOrGenNodeKey(cfg.NodeKeyFile())
	if err != nil {
		panic(err)
	}

	app := NewAttendanceApp(appDBPath)

	// 🔥 Start HTTP Server
	http.HandleFunc("/attendance", app.GetAllAttendance)
	go http.ListenAndServe(":8080", nil)

	logger := log.NewTMLogger(os.Stdout)

	dbProvider := func(ctx *node.DBContext) (tmdb.DB, error) {
		return tmdb.NewGoLevelDB(ctx.ID, cfg.DBDir())
	}

	tmNode, err := node.NewNode(
		cfg,
		pv,
		nodeKey,
		proxy.NewLocalClientCreator(app),
		node.DefaultGenesisDocProviderFunc(cfg),
		dbProvider,
		node.DefaultMetricsProvider(cfg.Instrumentation),
		logger,
	)
	if err != nil {
		panic(err)
	}

	if err := tmNode.Start(); err != nil {
		panic(err)
	}

	fmt.Println("Attendance blockchain node running...")
	select {}
}
