function populateChart(chartId, infoId, ticker, mode, startTime, endTime) {
    var chart = LightweightCharts.createChart(document.getElementById(chartId), {
        width: 1200,
        height: 300,
        timeScale: {
            timeVisible: true,
        },
        rightPriceScale: {
            borderColor: '#D1D4DC',
        },
        layout: {
            background: {
                type: 'solid',
                color: 'white',
            },
            textColor: '#000',
        },
        grid: {
            horzLines: {
                color: '#F0F3FA',
            },
            vertLines: {
                color: '#F0F3FA',
            },
        },
    });

    var candleSeries = chart.addCandlestickSeries({
        upColor: 'blue',
        downColor: 'black',
        wickUpColor: 'blue',
        wickDownColor: 'black',
        borderVisible: false,
    });

    candleSeries.applyOptions({
        priceFormat: {
            type: 'custom',
            minMove: 0.00000001,
            formatter: price => parseFloat(price).toFixed(5),
        },
    });

    let markerData = new Map();

    fetch(`http://127.0.0.1:5000/get_${mode}_positions?ticker=${ticker}&tf=5min&start=${startTime}&end=${endTime}&strat=true`)
        .then(response => response.json())
        .then(data => {
            const chartData = data.map((dataPoint) => {
                return {
                    time: dataPoint.time + 60 * 60 * 2, 
                    open: dataPoint.open,
                    high: dataPoint.high,
                    low: dataPoint.low,
                    close: dataPoint.close,
                };
            });

            const markers = data.reduce((markers, dataPoint) => {
                let timeKey = dataPoint.time + 60 * 60 * 2;
                if (dataPoint.signal == 'buy') {
                    markerData.set(timeKey, {
                        positionCloseTime: dataPoint.position_close_time,
                        positionClosePrice: dataPoint.position_close_price,
                        positionOrderPrice: dataPoint.position_order_price,
                        success: dataPoint.success,
                        profit: dataPoint.profit,
                        loss: dataPoint.loss,
                        outOfTime: dataPoint.out_of_time,
                        orderID: dataPoint.order_id
                    });
                    markers.push({
                        time: timeKey,
                        position: 'belowBar',
                        color: 'rgb(38,166,154)',
                        shape: 'arrowUp',
                    });
                } else if (dataPoint.signal == 'sell') {
                    markerData.set(timeKey, {
                        positionCloseTime: dataPoint.position_close_time,
                        positionClosePrice: dataPoint.position_close_price,
                        positionOrderPrice: dataPoint.position_order_price,
                        success: dataPoint.success,
                        profit: dataPoint.profit,
                        loss: dataPoint.loss,
                        outOfTime: dataPoint.out_of_time,
                        orderID: dataPoint.order_id
                    });
                    markers.push({
                        time: timeKey,
                        position: 'aboveBar',
                        color: 'rgb(255,82,82)',
                        shape: 'arrowDown'
                    });
                }
                
                return markers;
            }, []);
    
            candleSeries.setData(chartData);
            candleSeries.setMarkers(markers);

            console.log(markerData);

            let lastHoveredPositionData = null;

            chart.subscribeCrosshairMove(function(param) {
                if (param.point) {
                    var timeScale = chart.timeScale();
                    var timeAtCursor = timeScale.coordinateToTime(param.point.x);
            
                    if (markerData.has(timeAtCursor)) {
                        var markerInfo = markerData.get(timeAtCursor);
                        if (markerInfo) {
                            console.log(markerInfo.positionCloseTime);
                            var date = new Date(markerInfo.positionCloseTime + 60 * 60 * 2 * 1000);
                            console.log(date);
                            var formattedTime = date.toISOString(); 
                            lastHoveredPositionData = `Position close time: ${formattedTime}, 
                                                                          Position close price: ${markerInfo.positionClosePrice},
                                                                          Position order price: ${markerInfo.positionOrderPrice},
                                                                          Success: ${markerInfo.success}, 
                                                                          Profit: ${parseFloat(markerInfo.profit).toFixed(2)}, 
                                                                          Loss: ${parseFloat(markerInfo.loss).toFixed(2)}, 
                                                                          Out of Time: ${markerInfo.outOfTime},
                                                                          Order id: ${markerInfo.orderID}`;
                        }
                    }
                }
                if (lastHoveredPositionData) {
                    document.getElementById(infoId).innerText = lastHoveredPositionData;
                }
            });
    });
}

function getTickerAndPopulateCharts() {
    var ticker = document.getElementById('ticker').value;
    var startTime = document.getElementById('start-input').value;
    var endTime = document.getElementById('end-input').value;

    populateChart('backtest_chart', 'backtest_chart-info', ticker, 'backtest', startTime, endTime);
    populateChart('live_chart', 'live_chart-info', ticker, 'live', startTime, endTime);
}

document.getElementById('populate-charts').addEventListener('click', getTickerAndPopulateCharts);