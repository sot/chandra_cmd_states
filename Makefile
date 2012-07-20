# Set the task name
TASK = cmd_states
VERSI0N = 0.03

# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

SHARE = add_nonload_cmds.py  nonload_cmds_archive.py \
	update_cmd_states.py  interrupt_loads.py  get_cmd_states.py
DATA = *_def.sql task_schedule.cfg
DOC = docs/_build/html/
BIN = get_cmd_states

include /proj/sot/ska/include/Makefile.FLIGHT

.PHONY: test dist install docs

test: check_install $(BIN) $(TEST_DEP) install
	$(INSTALL_BIN)/task.pl

# Make a versioned distribution.  Could also use an EXCLUDE_MANIFEST
dist:
	mkdir $(NAME)-$(VERSION)
	tar --exclude CVS --exclude "*~" --create --files-from=MANIFEST --file - \
	 | (tar --extract --directory $(NAME)-$(VERSION) --file - )
	tar --create --verbose --gzip --file $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	rm -rf $(NAME)-$(VERSION)

docs:
	cd docs ; \
	make html

install:
#  Uncomment the lines which apply for this task
	mkdir -p $(INSTALL_DATA)
	mkdir -p $(INSTALL_SHARE)
	mkdir -p $(INSTALL_DOC)
	mkdir -p $(INSTALL_BIN)

	rsync --times --cvs-exclude $(BIN) $(INSTALL_BIN)/
	rsync --times --cvs-exclude $(DATA) $(INSTALL_DATA)/
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
	rsync --archive --times --cvs-exclude $(DOC) $(INSTALL_DOC)/

