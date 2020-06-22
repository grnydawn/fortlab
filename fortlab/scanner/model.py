"""Microapp compiler inspector"""

from microapp import App


class MicroappModelCombiner(App):

    _name_ = "modelcombine"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("modeldir", metavar="raw datadir", help="Raw model data directory")
        self.add_argument("-o", "--output", type=str, help="output path.")

        #self.register_forward("data", help="json object")

    def perform(self, args):

        import pdb; pdb.set_trace()
#        if os.path.exists(data_etime_path) and len(glob.glob( '%s/*'%data_etime_path )) > 0 and Config.model['reuse_rawdata']:
#
#            kgutils.logger.info('Generating model file: %s/%s'%(Config.path['outdir'], Config.modelfile))
#
#            # collect data
#            etimes = {} # mpirank:omptid:invoke=[(fileid, linenum, numvisits), ... ]
#            etimemin = 1.0E100
#            etimemax = 0.0
#            netimes = 0
#            etimeresol = 0.0
#            nexcluded_under = 0
#            nexcluded_over = 0
#
#            mpipaths = []
#            for item in os.listdir(data_etime_path):
#                try:
#                    mpirank, ompthread = item.split('.')
#                    if mpirank.isdigit() and ompthread.isdigit():
#                        mpipaths.append((data_etime_path, mpirank, ompthread))
#                except:
#                    pass
#
#            #nprocs = min( len(mpipaths), multiprocessing.cpu_count()*1)
#            nprocs = 1
#
#            if nprocs == 0:
#                kgutils.logger.warn('No elapsedtime data files are found.')
#            else:
#                workload = [ chunk for chunk in chunks(mpipaths, int(math.ceil(len(mpipaths)/nprocs))) ]
#                inqs = []
#                outqs = []
#                for _ in range(nprocs):
#                    inqs.append(multiprocessing.Queue())
#                    outqs.append(multiprocessing.Queue())
#
#                procs = []
#                for idx in range(nprocs):
#                    proc = multiprocessing.Process(target=readdatafiles, args=(inqs[idx], outqs[idx]))
#                    procs.append(proc)
#                    proc.start()
#
#                for inq, chunk in zip(inqs,workload):
#                    inq.put(chunk)
#
#                for outq in outqs:
#                    etime, emeta = outq.get()
#                    update(etimes, etime)
#                    etimemin = min(etimemin, emeta[0])
#                    etimemax = max(etimemax, emeta[1])
#                    netimes += emeta[2]
#                    etimeresol = max(etimeresol, emeta[3])
#                    nexcluded_under += emeta[4]
#                    nexcluded_over += emeta[5]
#                for idx in range(nprocs):
#                    procs[idx].join()
#
#                kgutils.logger.info('# of excluded samples: under limit = %d, over limit = %d'%(nexcluded_under, nexcluded_over))
#
#            #import pdb; pdb.set_trace()
#
#            if len(etimes) == 0:
#                if not _DEBUG:
#                    shutil.rmtree(data_etime_path)
#                kgutils.logger.warn('Elapsedtime data is not collected.')
#            else:
#                try:
#                    etime_sections = [ Config.path['etime'], 'summary']
#
#                    self.addmodel(Config.path['etime'], etime_sections)
#
#                    # elapsedtime section
#                    etime = []
#                    #fd.write('; <MPI rank> < OpenMP Thread> <invocation order> =  <file number>:<line number><num of invocations> ...\n')
#
#                    for ranknum, threadnums in etimes.items():
#                        for threadnum, invokenums in threadnums.items():
#                            for invokenum, evalues  in invokenums.items():
#                                etime.append( ( '%s %s %s'%(ranknum, threadnum, invokenum), ', '.join(evalues) ) )
#                    self.addsection(Config.path['etime'], Config.path['etime'], etime)
#
#                    summary = []
#                    summary.append( ('minimum_elapsedtime', str(etimemin)) )
#                    summary.append( ('maximum_elapsedtime', str(etimemax)) )
#                    summary.append( ('number_elapsedtimes', str(netimes)) )
#                    summary.append( ('resolution_elapsedtime', str(etimeresol)) )
#                    self.addsection(Config.path['etime'], 'summary', summary )
#
#                except Exception as e:
#                    kgutils.logger.error(str(e))
#        else:
#            if not _DEBUG:
#                shutil.rmtree(data_etime_path)
#            kgutils.logger.info('failed to generate elapsedtime information')
#
#        out, err, retcode = kgutils.run_shcmd('make recover', cwd=etime_realpath)
#
#        if Config.state_switch['clean']:
#            kgutils.run_shcmd(Config.state_switch['clean'])
#    else: # check if coverage should be invoked
#        kgutils.logger.info('Reusing Elapsedtime file: %s/%s'%(Config.path['outdir'], Config.modelfile))
#
#    # check if elapsedtime data exists in model file
#    if not os.path.exists('%s/%s'%(Config.path['outdir'], Config.modelfile)):
#        kgutils.logger.warn('No elapsedtime file is found.')
#    else:
#        # read ini file
#        kgutils.logger.info('Reading %s/%s'%(Config.path['outdir'], Config.modelfile))
#
#        cfg = configparser.ConfigParser()
#        cfg.optionxform = str
#        cfg.read('%s/%s'%(Config.path['outdir'], Config.modelfile))
#
#        try:
#
#            etimemin = float(cfg.get('elapsedtime.summary', 'minimum_elapsedtime').strip())
#            etimemax = float(cfg.get('elapsedtime.summary', 'maximum_elapsedtime').strip())
#            netimes = int(cfg.get('elapsedtime.summary', 'number_elapsedtimes').strip())
#            etimediff = etimemax - etimemin
#            etimeres = float(cfg.get('elapsedtime.summary', 'resolution_elapsedtime').strip())
#
#            # <MPI rank> < OpenMP Thread> <invocation order> =  <file number>:<line number>:<num etimes> ... 
#            if etimediff == 0:
#                nbins = 1
#            else:
#                nbins = max(min(Config.model['types']['etime']['nbins'], netimes), 2)
#
#            kgutils.logger.info('nbins = %d'%nbins)
#            kgutils.logger.info('etimemin = %f'%etimemin)
#            kgutils.logger.info('etimemax = %f'%etimemax)
#            kgutils.logger.info('etimediff = %f'%etimediff)
#            kgutils.logger.info('netimes = %d'%netimes)
#
#            if nbins > 1:
#                etimebins = [ {} for _ in range(nbins) ]
#                etimecounts = [ 0 for _ in range(nbins) ]
#            else:
#                etimebins = [ {} ]
#                etimecounts = [ 0 ]
#
#            idx = 0
#            for opt in cfg.options('elapsedtime.elapsedtime'):
#                ranknum, threadnum, invokenum = tuple( num for num in opt.split() )
#                start, stop = cfg.get('elapsedtime.elapsedtime', opt).split(',')
#                estart = float(start)
#                eend = float(stop)
#                etimeval = eend - estart
#                if nbins > 1:
#                    binnum = int(math.floor((etimeval - etimemin) / etimediff * (nbins - 1)))
#                else:
#                    binnum = 0
#                etimecounts[binnum] += 1
#            kgutils.logger.info('etimediff = %f'%etimediff)
#            kgutils.logger.info('netimes = %d'%netimes)
#
#            if nbins > 1:
#                etimebins = [ {} for _ in range(nbins) ]
#                etimecounts = [ 0 for _ in range(nbins) ]
#            else:
#                etimebins = [ {} ]
#                etimecounts = [ 0 ]
#
#            idx = 0
#            for opt in cfg.options('elapsedtime.elapsedtime'):
#                ranknum, threadnum, invokenum = tuple( num for num in opt.split() )
#                start, stop = cfg.get('elapsedtime.elapsedtime', opt).split(',')
#                estart = float(start)
#                eend = float(stop)
#                etimeval = eend - estart
#                if nbins > 1:
#                    binnum = int(math.floor((etimeval - etimemin) / etimediff * (nbins - 1)))
#                else:
#                    binnum = 0
#                etimecounts[binnum] += 1
#        triples = []
#        for binnum, etimebin in enumerate(etimebins):
#            bin_triples = []
#            range_begin = binnum*(etimemax-etimemin)/nbins + etimemin if binnum > 0  else etimemin
#            range_end = (binnum+1)*(etimemax-etimemin)/nbins + etimemin if binnum < (nbins-1)  else None
#
#            bunit = 'sec'
#            if range_begin < 1.E-6:
#                bunit = 'usec'
#                range_begin *= 1.E6
#
#            if range_end is None:
#                print 'From bin # %d [ %f (%s) ~ ] %f %% of %d'%(binnum, \
#                    range_begin, bunit, countdist[binnum] * 100, totalcount)
#            else:
#                eunit = 'sec'
#                if range_end < 1.E-6:
#                    eunit = 'usec'
#                    range_end *= 1.E6
#
#                print 'From bin # %d [ %f (%s) ~ %f (%s) ] %f %% of %d'%(binnum, \
#                    range_begin, bunit, range_end, eunit, countdist[binnum] * 100, totalcount)
#
#            for invokenum in sorted(etimebin.keys()):
#                if len(bin_triples) >= datacollect[binnum]: break
#                # select datacollect[binum] under this data tree, rank/thread/invoke
#                bininvokes = etimebin[invokenum].keys()
#                random.shuffle(bininvokes)
#                for ranknum in bininvokes:
#                    if len(bin_triples) >= datacollect[binnum]: break
#                    binranks = etimebin[invokenum][ranknum].keys()
#                    random.shuffle(binranks)
#                    for threadnum in binranks:
#                        bin_triples.append( (ranknum, threadnum, invokenum) )
#                        print '        invocation triple: %s:%s:%s'%(ranknum, threadnum, invokenum)
#            triples.extend(bin_triples)
#
#        print 'Number of bins: %d'%nbins
#        print 'Minimun elapsed time: %f'%etimemin
#        print 'Maximum elapsed time: %f'%etimemax
#        #print 'Selected invocation triples:'
#        #print ','.join([ ':'.join([ str(n) for n in t ]) for t in triples])
#
#        for ranknum, threadnum, invokenum in triples:
#            Config.invocation['triples'].append( ( (str(ranknum), str(ranknum)), (str(threadnum), str(threadnum)), \
#                (str(invokenum), str(invokenum)) ) )
#
